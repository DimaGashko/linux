#!/usr/bin/env python3
"""Accumulate workspace digits while switching immediately, without keyboard grabs."""

import argparse
import ctypes as C
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import select
import socket
import struct
import subprocess
import sys
import time


HEADER = struct.Struct("=6sII")
BINDING = (1 << 31) | 5
MOD4 = 1 << 6
PREFIX = "nop workspace-input "


class IPC:
    def __init__(self, path):
        self.socket = socket.socket(socket.AF_UNIX)
        self.socket.settimeout(2)
        self.socket.connect(path)

    def send(self, kind, payload=""):
        data = payload.encode()
        self.socket.sendall(HEADER.pack(b"i3-ipc", len(data), kind) + data)

    def receive(self):
        def read(size):
            data = bytearray()

            while len(data) < size:
                part = self.socket.recv(size - len(data))

                if not part:
                    raise ConnectionError("i3 disconnected")

                data.extend(part)

            return data

        magic, length, kind = HEADER.unpack(read(HEADER.size))

        if magic != b"i3-ipc":
            raise ConnectionError("Invalid i3 IPC header")

        return kind, json.loads(read(length))

    def request(self, kind, payload=""):
        self.send(kind, payload)
        reply_kind, reply = self.receive()

        if reply_kind != kind:
            raise ConnectionError("Unexpected i3 IPC reply")

        return reply

    def command(self, command):
        replies = self.request(0, command)

        for reply in replies:
            if not reply["success"]:
                raise RuntimeError(reply.get("error", "i3 command failed"))

    def close(self):
        self.socket.close()


class XkbStateEvent(C.Structure):
    _fields_ = [
        ("type", C.c_int), ("serial", C.c_ulong), ("send_event", C.c_int),
        ("display", C.c_void_p), ("time", C.c_ulong), ("xkb_type", C.c_int),
        ("device", C.c_int), ("changed", C.c_uint), ("group", C.c_int),
        ("base_group", C.c_int), ("latched_group", C.c_int),
        ("locked_group", C.c_int), ("mods", C.c_uint),
    ]


class XEvent(C.Union):
    _fields_ = [("state", XkbStateEvent), ("padding", C.c_long * 24)]


class ModifierObserver:
    """Observe XKB modifier changes; no key grabs, key replay, or idle polling."""

    def __init__(self):
        self.x = C.CDLL("libX11.so.6")
        signatures = {
            "XOpenDisplay": ([C.c_char_p], C.c_void_p),
            "XConnectionNumber": ([C.c_void_p], C.c_int),
            "XPending": ([C.c_void_p], C.c_int),
            "XNextEvent": ([C.c_void_p, C.c_void_p], C.c_int),
            "XFlush": ([C.c_void_p], C.c_int),
            "XCloseDisplay": ([C.c_void_p], C.c_int),
            "XDefaultRootWindow": ([C.c_void_p], C.c_ulong),
            "XQueryPointer": ([C.c_void_p, C.c_ulong] + [C.POINTER(C.c_ulong)] * 2
                              + [C.POINTER(C.c_int)] * 4 + [C.POINTER(C.c_uint)], C.c_int),
            "XWarpPointer": ([C.c_void_p, C.c_ulong, C.c_ulong, C.c_int, C.c_int,
                              C.c_uint, C.c_uint, C.c_int, C.c_int], C.c_int),
            "XkbQueryExtension": ([C.c_void_p] + [C.POINTER(C.c_int)] * 5, C.c_int),
            "XkbSelectEventDetails": ([C.c_void_p, C.c_uint, C.c_uint,
                                       C.c_ulong, C.c_ulong], C.c_int),
            "XkbGetState": ([C.c_void_p, C.c_uint, C.c_void_p], C.c_int),
        }

        for name, (args, result) in signatures.items():
            function = getattr(self.x, name)
            function.argtypes = args
            function.restype = result

        self.display = self.x.XOpenDisplay(None)

        if not self.display:
            raise RuntimeError("Cannot open X11 display")

        opcode, event_base, error_base = C.c_int(), C.c_int(), C.c_int()
        major, minor = C.c_int(1), C.c_int(0)

        if not self.x.XkbQueryExtension(self.display, C.byref(opcode),
                                       C.byref(event_base), C.byref(error_base),
                                       C.byref(major), C.byref(minor)):
            raise RuntimeError("XKB is unavailable")

        self.event_base = event_base.value
        self.x.XkbSelectEventDetails(self.display, 0x100, 2, 1, 1)
        self.x.XFlush(self.display)
        self.fd = self.x.XConnectionNumber(self.display)

    def warp_to_output(self, rect):
        root = self.x.XDefaultRootWindow(self.display)
        root_return, child = C.c_ulong(), C.c_ulong()
        root_x, root_y, window_x, window_y = (C.c_int() for _ in range(4))
        mask = C.c_uint()
        same_screen = self.x.XQueryPointer(
            self.display, root, C.byref(root_return), C.byref(child),
            C.byref(root_x), C.byref(root_y), C.byref(window_x), C.byref(window_y), C.byref(mask)
        )

        x, y, width, height = rect["x"], rect["y"], rect["width"], rect["height"]

        if same_screen and x <= root_x.value < x + width and y <= root_y.value < y + height:
            return

        self.x.XWarpPointer(self.display, 0, root, 0, 0, 0, 0, x + width // 2, y + height // 2)
        self.x.XFlush(self.display)

    def mod_held(self):
        # XkbStateRec starts with group, locked_group, base_group (short),
        # latched_group (short), then mods (unsigned char).
        state = C.create_string_buffer(64)

        if self.x.XkbGetState(self.display, 0x100, state) != 0:
            raise RuntimeError("Cannot read XKB modifier state")

        return bool(state.raw[6] & MOD4)

    def releases(self):
        while self.x.XPending(self.display):
            event = XEvent()
            self.x.XNextEvent(self.display, C.byref(event))

            if (event.state.type == self.event_base and event.state.xkb_type == 2
                    and not event.state.mods & MOD4):
                yield None

    def close(self):
        self.x.XCloseDisplay(self.display)


def focused_container(node):
    if node.get("focused"):
        return node["id"] if node["type"] in ("con", "floating_con") else None

    for child in node.get("nodes", []) + node.get("floating_nodes", []):
        found = focused_container(child)

        if found is not None:
            return found

    return None


class WorkspaceInput:
    def __init__(self, ipc, timeout):
        self.ipc = ipc
        self.timeout = timeout
        self.down = set()
        self.cancel()

    def cancel(self):
        self.digits = ""
        self.action = None
        self.container = None
        self.deadline = None

    def visit(self, target, action, container=None):
        workspace = f'workspace --no-auto-back-and-forth "{target}"'

        if action == "move" and container is not None:
            self.ipc.command(
                f'[con_id={container}] move container to workspace "{target}"; '
                f'{workspace}; [con_id={container}] focus'
            )
        else:
            self.ipc.command(workspace)

    def binding(self, command, now):
        if not command.startswith(PREFIX):
            self.cancel()
            return

        parts = command[len(PREFIX):].split()

        if len(parts) != 2:
            self.cancel()
            return

        action, value = parts

        if action == "release":
            self.down.discard(value)
            return

        if action not in ("switch", "move"):
            self.cancel()
            return

        if (value != "grave" and not re.fullmatch(r"[0-9]", value)) or value in self.down:
            return

        self.down.add(value)

        if self.deadline is not None and (now >= self.deadline or action != self.action):
            self.cancel()

        if not self.digits:
            self.action = action
            self.container = focused_container(self.ipc.request(4)) if action == "move" else None

        self.digits += "0" if value == "grave" else value
        self.deadline = now + self.timeout

        # Keep names as strings: i3 accepts digit-only names beyond integer range.
        target = self.digits.lstrip("0") or "0"

        if self.digits == "0" and value == "0":
            target = "10"

        if self.digits in ("01", "02", "03"):
            target = {"01": "A", "02": "B", "03": "C"}[self.digits]

        self.visit(target, self.action, self.container)

    def release_mod(self):
        self.cancel()
        self.down.clear()


def listen(path, observer, timeout):
    commands, events = IPC(path), IPC(path)

    try:
        reply = events.request(2, '["binding", "mode", "shutdown"]')

        if not reply.get("success"):
            raise RuntimeError("Cannot subscribe to i3 events")

        state = WorkspaceInput(commands, timeout)
        print(f"Workspace input ready ({timeout * 1000:g} ms).", file=sys.stderr, flush=True)

        while True:
            delay = None if state.deadline is None else max(0, state.deadline - time.monotonic())

            if observer.x.XPending(observer.display):
                delay = 0

            select.select([events.socket, observer.fd], [], [], delay)

            # Drain bindings first: they may have arrived before a Mod release.
            while select.select([events.socket], [], [], 0)[0]:
                kind, event = events.receive()

                if kind == BINDING:
                    command = event["binding"]["command"]
                    state.binding(command, time.monotonic())

                    if command == "move workspace to output right":
                        outputs = [output for output in commands.request(3) if output["active"]]

                        if len(outputs) > 1:
                            focused = next((ws for ws in commands.request(1) if ws["focused"]), None)

                            for output in outputs:
                                if focused and output["name"] == focused["output"]:
                                    observer.warp_to_output(output["rect"])
                                    break
                else:
                    state.cancel()
                    state.down.clear()

            for _ in observer.releases():
                state.release_mod()

            # Covers a very quick tap where XKB delivered the release before IPC.
            if state.digits and not observer.mod_held():
                state.release_mod()

            if state.deadline is not None and time.monotonic() >= state.deadline:
                state.cancel()
    finally:
        commands.close()
        events.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=float, default=300)
    args = parser.parse_args()

    if not 0 < args.timeout_ms < 60000:
        parser.error("--timeout-ms must be between 0 and 60000")

    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", Path.home() / ".cache"))
    runtime.mkdir(parents=True, exist_ok=True)
    display_key = hashlib.sha256(os.environ.get("DISPLAY", "").encode()).hexdigest()[:16]

    with (runtime / f"i3-workspace-input-{display_key}.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return

        observer = ModifierObserver()

        try:
            while True:
                try:
                    path = subprocess.check_output(["i3", "--get-socketpath"], text=True).strip()
                    listen(path, observer, args.timeout_ms / 1000)
                except (OSError, ConnectionError, RuntimeError, subprocess.CalledProcessError) as error:
                    print(f"Workspace input: {error}; reconnecting.", file=sys.stderr, flush=True)
                    time.sleep(1)
        finally:
            observer.close()


if __name__ == "__main__":
    main()
