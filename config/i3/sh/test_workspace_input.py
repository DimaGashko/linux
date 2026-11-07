#!/usr/bin/env python3
"""Test real key events, i3 IPC, and workspace moves on an isolated Xvfb display."""

import ctypes as C
import importlib.util
import os
from pathlib import Path
import re
import select
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("workspace_input", ROOT / "workspace-input.py")
workspace_input = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workspace_input)


class WorkspaceInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.x = C.CDLL("libX11.so.6")
        cls.xtest = C.CDLL("libXtst.so.6")
        signatures = {
            "XOpenDisplay": ([C.c_char_p], C.c_void_p),
            "XStringToKeysym": ([C.c_char_p], C.c_ulong),
            "XKeysymToKeycode": ([C.c_void_p, C.c_ulong], C.c_uint),
            "XSync": ([C.c_void_p, C.c_int], C.c_int),
            "XCloseDisplay": ([C.c_void_p], C.c_int),
            "XDefaultRootWindow": ([C.c_void_p], C.c_ulong),
            "XCreateSimpleWindow": ([C.c_void_p, C.c_ulong, C.c_int, C.c_int,
                                      C.c_uint, C.c_uint, C.c_uint,
                                      C.c_ulong, C.c_ulong], C.c_ulong),
            "XMapWindow": ([C.c_void_p, C.c_ulong], C.c_int),
            "XDestroyWindow": ([C.c_void_p, C.c_ulong], C.c_int),
            "XkbLockGroup": ([C.c_void_p, C.c_uint, C.c_uint], C.c_int),
        }

        for name, (args, result) in signatures.items():
            function = getattr(cls.x, name)
            function.argtypes = args
            function.restype = result

        cls.xtest.XTestFakeKeyEvent.argtypes = [C.c_void_p, C.c_uint, C.c_int, C.c_ulong]
        cls.display = cls.x.XOpenDisplay(None)
        assert cls.display

    @classmethod
    def tearDownClass(cls):
        cls.x.XCloseDisplay(cls.display)

    def setUp(self):
        self.held = set()
        self.windows = []
        self.temporary = tempfile.TemporaryDirectory(prefix="workspace-input-test-")
        self.addCleanup(self.temporary.cleanup)
        self.path = str(Path(self.temporary.name) / "i3.sock")
        self.env = dict(os.environ, I3SOCK=self.path, XDG_RUNTIME_DIR=self.temporary.name)
        config = Path(self.temporary.name) / "config"
        config.write_text(
            f"font pango:monospace 8\nipc-socket {self.path}\n"
            "set $mod Mod4\nfocus_follows_mouse no\nworkspace start\n"
            "bindsym $mod+f fullscreen toggle\n"
            "bindsym $mod+q workspace ordinary\n"
            "bindsym $mod+Escape nop cancel\n"
            + (ROOT.parent / "i3.d/workspaces.i3").read_text()
        )
        self.log = (Path(self.temporary.name) / "i3.log").open("w+")
        self.addCleanup(self.log.close)
        self.i3 = subprocess.Popen(["i3", "-c", str(config)], env=self.env,
                                   stdout=self.log, stderr=self.log)
        self.addCleanup(self.stop_i3)
        self.wait_until(lambda: Path(self.path).exists())
        self.ipc = workspace_input.IPC(self.path)
        self.addCleanup(self.ipc.close)
        self.ipc.command('workspace "start"')
        self.daemon = subprocess.Popen([str(ROOT / "workspace-input.py")], env=self.env,
                                       stderr=subprocess.PIPE)
        self.addCleanup(self.stop_daemon)
        ready, _, _ = select.select([self.daemon.stderr], [], [], 3)
        self.assertTrue(ready, "Helper startup timed out")
        self.assertEqual(self.daemon.stderr.readline(), b"Workspace input ready (300 ms).\n")

    def stop_i3(self):
        self.i3.terminate()
        self.i3.wait(timeout=3)

    def stop_daemon(self):
        for key in tuple(self.held):
            self.key(key, False)

        self.daemon.terminate()
        self.daemon.wait(timeout=3)
        self.daemon.stderr.close()

        for window in self.windows:
            self.x.XDestroyWindow(self.display, window)

        self.x.XSync(self.display, False)

    def wait_until(self, predicate, timeout=2):
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            if predicate():
                return

            time.sleep(.005)

        self.fail("Timed out waiting for expected i3 state")

    def key(self, name, down, pause=.008):
        code = self.x.XKeysymToKeycode(self.display, self.x.XStringToKeysym(name.encode()))
        self.xtest.XTestFakeKeyEvent(self.display, code, down, 0)
        self.x.XSync(self.display, False)

        if down:
            self.held.add(name)
        else:
            self.held.discard(name)

        time.sleep(pause)

    def tap(self, name):
        self.key(name, True)
        self.key(name, False)

    def current(self):
        return next(ws["name"] for ws in self.ipc.request(1) if ws["focused"])

    def expect(self, name):
        self.wait_until(lambda: self.current() == name)

    def chord(self, digits, move=False):
        self.key("Super_L", True)

        if move:
            self.key("Shift_L", True)

        for digit in digits:
            self.tap(digit)

        self.key("Super_L", False)

        if move:
            self.key("Shift_L", False)

    def nodes(self, node=None):
        if node is None:
            node = self.ipc.request(4)

        yield node

        for child in node.get("nodes", []) + node.get("floating_nodes", []):
            yield from self.nodes(child)

    def create_window(self):
        root = self.x.XDefaultRootWindow(self.display)
        window = self.x.XCreateSimpleWindow(self.display, root, 0, 0, 100, 100, 0, 0, 0)
        self.windows.append(window)
        self.x.XMapWindow(self.display, window)
        self.x.XSync(self.display, False)
        self.wait_until(lambda: any(n.get("window") == window for n in self.nodes()))
        return next(n["id"] for n in self.nodes() if n.get("window") == window)

    def test_single_digit_switches_before_timeout(self):
        self.key("Super_L", True)
        self.tap("1")
        self.wait_until(lambda: self.current() == "1", timeout=.15)

    def test_fast_digits_and_timer_reset(self):
        self.key("Super_L", True)
        target = ""

        for digit in "12345":
            target += digit
            self.tap(digit)
            self.wait_until(lambda: self.current() == target, timeout=.15)
            time.sleep(.15)

        self.expect("12345")

    def test_slow_digits_are_separate(self):
        self.key("Super_L", True)
        self.tap("1")
        self.expect("1")
        time.sleep(.35)
        self.tap("2")
        self.expect("2")

    def test_release_separates_chords(self):
        self.chord("1")
        self.expect("1")
        self.chord("2")
        self.expect("2")

    def test_zero_grave_repeated_digits_and_large_names(self):
        self.chord("0")
        self.expect("10")
        self.chord(["grave"])
        self.expect("0")
        self.chord(["1", "grave", "0"])
        self.expect("100")
        self.chord("11")
        self.expect("11")
        self.chord("000")
        self.expect("0")
        self.chord("123456789012345678901234567890")
        self.expect("123456789012345678901234567890")

    def test_initial_zero_moves_to_ten_and_grave_to_zero(self):
        container = self.create_window()
        self.chord("0", move=True)
        self.expect("10")
        self.assertEqual(workspace_input.focused_container(self.ipc.request(4)), container)
        self.chord(["grave"], move=True)
        self.expect("0")
        self.assertEqual(workspace_input.focused_container(self.ipc.request(4)), container)

    def test_other_i3_hotkey_ends_sequence(self):
        self.key("Super_L", True)
        self.tap("1")
        self.tap("q")
        self.expect("ordinary")
        time.sleep(.35)
        self.assertEqual(self.current(), "ordinary")
        self.tap("2")
        self.expect("2")

    def test_other_i3_hotkey_acts_on_current_window(self):
        self.ipc.command('workspace "1"')
        container = self.create_window()
        self.ipc.command('workspace "start"')
        self.key("Super_L", True)
        self.tap("1")
        self.expect("1")
        self.tap("f")
        time.sleep(.35)
        self.assertEqual(self.current(), "1")
        node = next(n for n in self.nodes() if n["id"] == container)
        self.assertEqual(node["fullscreen_mode"], 1)

    def test_move_and_follow_keeps_window_focused(self):
        container = self.create_window()
        self.key("Super_L", True)
        self.key("Shift_L", True)
        target = ""

        for digit in "12345":
            target += digit
            self.tap(digit)
            self.wait_until(lambda: self.current() == target, timeout=.15)
            self.assertEqual(workspace_input.focused_container(self.ipc.request(4)), container)
            time.sleep(.15)

    def test_move_captures_original_focus(self):
        original = self.create_window()
        self.key("Super_L", True)
        self.key("Shift_L", True)
        self.tap("8")
        self.expect("8")
        other = self.create_window()
        self.tap("9")
        self.expect("89")
        self.assertEqual(workspace_input.focused_container(self.ipc.request(4)), original)
        intermediate = next(n for n in self.nodes() if n["type"] == "workspace" and n["name"] == "8")
        self.assertIn(other, [n["id"] for n in self.nodes(intermediate)])

    def test_expiry_does_not_switch_again(self):
        self.key("Super_L", True)
        self.tap("1")
        self.expect("1")
        self.ipc.command('workspace "elsewhere"')
        time.sleep(.35)
        self.assertEqual(self.current(), "elsewhere")

    def test_common_workspaces_accept_leading_zero_input(self):
        for digits in ("01", "02", "03"):
            self.chord(digits)
            self.expect({"01": "A", "02": "B", "03": "C"}[digits])

        self.chord("012")
        self.expect("12")

    def test_move_from_empty_workspace(self):
        self.chord("15", move=True)
        self.expect("15")

    def test_common_workspaces_and_shift_variants(self):
        container = self.create_window()

        for key, target in [("minus", "A"), ("equal", "B"), ("BackSpace", "C"), ("Home", "124")]:
            self.chord([key], move=True)
            self.expect(target)
            self.assertEqual(workspace_input.focused_container(self.ipc.request(4)), container)
            self.ipc.command('workspace "start"')
            self.chord([key])
            self.expect(target)

    def test_polybar_shows_common_workspaces_after_numbers(self):
        for name in ("A", "B", "C", "12345", "2", "1"):
            self.ipc.command(f'workspace "{name}"')
            self.create_window()

        self.assertEqual([ws["name"] for ws in self.ipc.request(1)],
                         ["1", "2", "12345", "A", "B", "C"])
        config = Path(self.temporary.name) / "polybar.ini"
        source = (ROOT.parents[1] / "polybar/config.ini").read_text()
        config.write_text(source + "\n[bar/test]\nwidth = 800\nheight = 24\n"
                          "font-0 = monospace:size=8\nmodules-left = i3\n")
        bar_log = (Path(self.temporary.name) / "polybar.log").open("w+")
        bar = subprocess.Popen(["polybar", "--stdout", f"--config={config}", "test"],
                               env=self.env, stdout=subprocess.PIPE, stderr=bar_log, bufsize=0)

        try:
            deadline = time.monotonic() + 5
            labels = []

            while time.monotonic() < deadline:
                ready, _, _ = select.select([bar.stdout], [], [], .1)

                if not ready:
                    continue

                output = bar.stdout.readline().decode()

                if not output:
                    bar_log.seek(0)
                    self.fail(f"Polybar exited before rendering: {bar_log.read()}")

                labels = re.sub(r"%\{[^}]*\}", "", output).split()

                if labels:
                    break

            self.assertEqual(labels, ["1", "2", "12345", "A", "B", "C"])
        finally:
            bar.terminate()
            bar.wait(timeout=3)
            bar.stdout.close()
            bar_log.close()

    def test_holding_digit_does_not_repeat(self):
        self.key("Super_L", True)
        self.key("1", True)
        self.expect("1")
        time.sleep(.8)
        self.assertEqual(self.current(), "1")

    def test_two_mod_keys_and_right_mod(self):
        self.key("Super_L", True)
        self.key("Super_R", True)
        self.tap("1")
        self.key("Super_L", False)
        self.tap("2")
        self.key("Super_R", False)
        self.expect("12")

    def test_keyboard_layouts_and_lock_keys(self):
        subprocess.run(["setxkbmap", "-layout", "us,ru,ua", "-option", ""], check=True)
        self.tap("Caps_Lock")
        self.tap("Num_Lock")

        try:
            for group, target in [(0, "12"), (1, "34"), (2, "56")]:
                self.x.XkbLockGroup(self.display, 0x100, group)
                self.x.XSync(self.display, False)
                self.chord(target)
                self.expect(target)
        finally:
            self.x.XkbLockGroup(self.display, 0x100, 0)
            self.tap("Caps_Lock")
            self.tap("Num_Lock")

    def test_reload_and_duplicate_start(self):
        subprocess.run([str(ROOT / "workspace-input.py")], env=self.env, check=True, timeout=2)
        self.ipc.command("reload")
        self.chord("45")
        self.expect("45")

    def test_restart_reconnects(self):
        self.ipc.command("restart")
        deadline = time.monotonic() + 4

        while time.monotonic() < deadline:
            ready, _, _ = select.select([self.daemon.stderr], [], [], .1)

            if ready and self.daemon.stderr.readline() == b"Workspace input ready (300 ms).\n":
                break
        else:
            self.fail("Helper did not reconnect after i3 restart")

        self.ipc = workspace_input.IPC(self.path)
        self.addCleanup(self.ipc.close)
        self.chord("67")
        self.expect("67")

    def test_layout_switcher_coexists(self):
        launcher = ROOT.parents[2] / "sh/keyboard/layout-switcher.sh"
        helper = subprocess.Popen([str(launcher)], env=dict(self.env, XDG_CACHE_HOME=self.temporary.name),
                                  stderr=subprocess.PIPE)

        try:
            ready, _, _ = select.select([helper.stderr], [], [], 5)
            self.assertTrue(ready, "Layout helper startup timed out")
            self.assertEqual(helper.stderr.readline(), b"Layout switcher ready (us,ru,ua).\n")
            self.key("Super_L", True)
            self.tap("1")
            self.tap("space")
            self.key("Super_L", False)
            self.expect("1")
            self.chord("23")
            self.expect("23")
        finally:
            helper.terminate()
            helper.wait(timeout=3)
            helper.stderr.close()
            self.x.XkbLockGroup(self.display, 0x100, 0)


if __name__ == "__main__":
    if "--isolated" not in sys.argv or os.environ.get("WORKSPACE_TEST_XVFB") != "1":
        result = subprocess.run(
            ["xvfb-run", "-a", "-s", "-screen 0 800x600x24 -noreset",
             sys.executable, str(Path(__file__).resolve()), "--isolated"],
            env=dict(os.environ, WORKSPACE_TEST_XVFB="1"),
        )
        sys.exit(result.returncode)

    sys.argv.remove("--isolated")
    unittest.main(verbosity=2)
