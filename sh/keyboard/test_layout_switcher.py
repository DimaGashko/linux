#!/usr/bin/env python3
"""Exercise real XKB/key-grab behavior in an isolated Xvfb display."""

import ctypes as C
import ctypes.util
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parent


class LayoutSwitcherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="layout-switcher-test-")
        cls.environment = dict(os.environ, XDG_CACHE_HOME=cls.temporary.name,
                               XDG_RUNTIME_DIR=cls.temporary.name)
        cls.x11 = C.CDLL(ctypes.util.find_library("X11"))
        cls.xtest = C.CDLL(ctypes.util.find_library("Xtst"))
        cls.x11.XOpenDisplay.restype = C.c_void_p
        cls.x11.XStringToKeysym.argtypes = [C.c_char_p]
        cls.x11.XStringToKeysym.restype = C.c_ulong
        cls.x11.XKeysymToKeycode.argtypes = [C.c_void_p, C.c_ulong]
        cls.x11.XKeysymToKeycode.restype = C.c_ubyte
        cls.x11.XkbGetState.argtypes = [C.c_void_p, C.c_uint, C.c_void_p]
        cls.x11.XkbLockGroup.argtypes = [C.c_void_p, C.c_uint, C.c_uint]
        cls.x11.XDefaultRootWindow.argtypes = [C.c_void_p]
        cls.x11.XDefaultRootWindow.restype = C.c_ulong
        cls.x11.XSelectInput.argtypes = [C.c_void_p, C.c_ulong, C.c_long]
        cls.x11.XSetInputFocus.argtypes = [C.c_void_p, C.c_ulong, C.c_int, C.c_ulong]
        cls.x11.XPending.argtypes = [C.c_void_p]
        cls.x11.XNextEvent.argtypes = [C.c_void_p, C.c_void_p]
        cls.x11.XSync.argtypes = [C.c_void_p, C.c_int]
        cls.x11.XCloseDisplay.argtypes = [C.c_void_p]
        cls.xtest.XTestFakeKeyEvent.argtypes = [C.c_void_p, C.c_uint, C.c_int, C.c_ulong]
        cls.display = cls.x11.XOpenDisplay(None)
        assert cls.display

    @classmethod
    def tearDownClass(cls):
        cls.x11.XCloseDisplay(cls.display)
        cls.temporary.cleanup()

    def setUp(self):
        self.held = set()
        self.x11.XkbLockGroup(self.display, 0x0100, 0)
        self.x11.XSync(self.display, False)
        self.daemon = subprocess.Popen([str(ROOT / "layout-switcher.sh")],
                                       env=self.environment, stderr=subprocess.PIPE)
        self.addCleanup(self.stop_daemon)
        ready, _, _ = select.select([self.daemon.stderr], [], [], 10)
        self.assertTrue(ready, "Helper startup timed out")
        self.assertEqual(self.daemon.stderr.readline(), b"Layout switcher ready (us,ru,ua).\n")
        self.expect(0)

    def stop_daemon(self):
        for key in tuple(self.held):
            self.key(key, False)

        self.daemon.terminate()
        self.daemon.wait(timeout=3)
        self.daemon.stderr.close()

    def key(self, name, down):
        code = self.x11.XKeysymToKeycode(self.display, self.x11.XStringToKeysym(name.encode()))
        self.xtest.XTestFakeKeyEvent(self.display, code, down, 0)
        self.x11.XSync(self.display, False)

        if down:
            self.held.add(name)
        else:
            self.held.discard(name)

        time.sleep(0.02)

    def tap(self, name="space"):
        self.key(name, True)
        self.key(name, False)

    def expect(self, group):
        deadline = time.monotonic() + 1

        while time.monotonic() < deadline:
            state = C.create_string_buffer(64)
            self.assertEqual(self.x11.XkbGetState(self.display, 0x0100, state), 0)

            if state.raw[0] == group:
                return

            time.sleep(0.01)

        self.fail(f"Expected layout {group}, got {state.raw[0]}")

    def switch(self, count=1, reverse=False, modifier="Super_L"):
        self.key(modifier, True)

        if reverse:
            self.key("Shift_L", True)

        for _ in range(count):
            self.tap()

        if reverse:
            self.key("Shift_L", False)

        self.key(modifier, False)

    def test_recent_pair_and_third_layout(self):
        self.switch()
        self.expect(1)
        self.switch()
        self.expect(0)
        self.switch(2)
        self.expect(2)
        self.switch()
        self.expect(0)
        self.switch()
        self.expect(2)

    def test_reverse_and_wrap(self):
        self.switch(reverse=True)
        self.expect(2)
        self.switch(3)
        self.expect(2)
        self.switch()
        self.expect(0)

    def test_locks_and_right_mod(self):
        self.tap("Caps_Lock")
        self.tap("Num_Lock")

        try:
            self.switch(modifier="Super_R")
            self.expect(1)
            self.switch(2, modifier="Super_R")
            self.expect(2)
        finally:
            self.tap("Caps_Lock")
            self.tap("Num_Lock")

    def test_release_of_last_mod_commits(self):
        self.key("Super_L", True)
        self.key("Super_R", True)
        self.tap()
        self.expect(1)
        self.key("Super_L", False)
        self.tap()
        self.expect(2)
        self.key("Super_R", False)
        self.switch()
        self.expect(0)

    def test_held_space_does_not_repeat(self):
        self.key("Super_L", True)
        self.key("space", True)
        self.expect(1)
        time.sleep(1)
        self.expect(1)
        self.key("Super_L", False)
        self.key("space", False)
        self.switch()
        self.expect(0)

    def test_direct_selection_and_keymap_reload(self):
        subprocess.run([str(ROOT / "layout-switcher.sh"), "--select", "ua"],
                       env=self.environment, check=True)
        self.expect(2)
        self.switch()
        self.expect(0)
        subprocess.run(["setxkbmap", "-layout", "us,ru,ua", "-option", ""], check=True)
        time.sleep(0.1)
        self.switch()
        self.expect(2)

    def test_duplicate_start_is_harmless(self):
        subprocess.run([str(ROOT / "layout-switcher.sh")], env=self.environment,
                       check=True, timeout=3)
        self.assertIsNone(self.daemon.poll())
        self.switch()
        self.expect(1)

    def test_ordinary_typing_is_delivered(self):
        root = self.x11.XDefaultRootWindow(self.display)
        self.x11.XSelectInput(self.display, root, 1)
        self.x11.XSetInputFocus(self.display, root, 0, 0)
        self.x11.XSync(self.display, True)
        self.tap("a")
        types = []

        while self.x11.XPending(self.display):
            event = C.create_string_buffer(192)
            self.x11.XNextEvent(self.display, event)
            types.append(C.c_int.from_buffer(event).value)

        self.assertEqual(types.count(2), 1, "Ordinary key press was swallowed")


if __name__ == "__main__":
    if "--isolated" not in sys.argv or os.environ.get("KEYBOARD_TEST_XVFB") != "1":
        result = subprocess.run(
            ["xvfb-run", "-a", "-s", "-screen 0 800x600x24 -noreset",
             sys.executable, str(Path(__file__).resolve()), "--isolated"],
            env=dict(os.environ, KEYBOARD_TEST_XVFB="1"),
        )
        sys.exit(result.returncode)

    sys.argv.remove("--isolated")
    unittest.main(verbosity=2)
