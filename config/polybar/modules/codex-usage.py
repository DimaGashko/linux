#!/usr/bin/env python3
"""Print compact Codex account limits for Polybar."""

import json
import os
import queue
import select
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path


TIMEOUT_SECONDS = 15
NORMAL_POLL_SECONDS = 5 * 60
FAST_POLL_SECONDS = 30
FAST_MODE_DURATION_SECONDS = 20 * 60
OPENAI_ICON = "%{T2}\ue001%{T3}"
FAST_MODE_DOT = "%{O-18}%{F#b22222}%{T2}\ue002%{T3}%{F-}"
CACHE_PATH = Path(
    os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))
) / "polybar-codex-usage.json"
PID_PATH = CACHE_PATH.with_suffix(".pid")


def rpc_message(method, message_id=None, params=None):
    message = {"method": method, "params": params or {}}
    if message_id is not None:
        message["id"] = message_id
    return json.dumps(message, separators=(",", ":")) + "\n"


def codex_executable():
    from_path = shutil.which("codex")
    if from_path:
        return from_path

    candidates = (
        Path("/usr/lib/chatgpt/resources/codex"),
        Path.home() / ".local/bin/codex",
        Path("/usr/local/bin/codex"),
        Path("/usr/bin/codex"),
    )
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise FileNotFoundError("Codex executable not found")


class CodexAppServer:
    def __init__(self):
        self.next_id = 1
        self.process = subprocess.Popen(
            [codex_executable(), "app-server", "--listen", "stdio://"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        try:
            self.initialize()
        except BaseException:
            self.close()
            raise

    def initialize(self):
        self.request(
            "initialize",
            {
                "clientInfo": {
                    "name": "polybar_codex_usage",
                    "title": "Polybar Codex Usage",
                    "version": "1.0.0",
                }
            },
        )
        self.send("initialized")

    def send(self, method, message_id=None, params=None):
        if self.process.poll() is not None:
            raise RuntimeError("Codex app-server stopped")
        self.process.stdin.write(rpc_message(method, message_id, params))
        self.process.stdin.flush()

    def request(self, method, params=None):
        message_id = self.next_id
        self.next_id += 1
        self.send(method, message_id, params)
        deadline = time.monotonic() + TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            ready, _, _ = select.select(
                [self.process.stdout], [], [], max(0, deadline - time.monotonic())
            )
            if not ready:
                break
            line = self.process.stdout.readline()
            if not line:
                break
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            if message.get("id") == message_id:
                if "error" in message:
                    raise RuntimeError(str(message["error"]))
                return message["result"]
        raise TimeoutError(f"Codex request timed out: {method}")

    def fetch_limits(self):
        return self.request("account/rateLimits/read")

    def close(self):
        if self.process.poll() is not None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()


def selected_snapshot(payload):
    buckets = payload.get("rateLimitsByLimitId") or {}
    return buckets.get("codex") or payload.get("rateLimits") or {}


def limit_windows(payload):
    snapshot = selected_snapshot(payload)
    windows = [window for window in (snapshot.get("primary"), snapshot.get("secondary")) if window]
    windows.sort(key=lambda window: window.get("windowDurationMins") or 0)

    return windows


def window_label(window):
    minutes = window.get("windowDurationMins")

    if not minutes:
        return "Usage"

    if minutes % (24 * 60) == 0:
        return f"{minutes // (24 * 60)}d"

    if minutes % 60 == 0:
        return f"{minutes // 60}h"

    return f"{minutes}m"


def reset_countdown(window, now=None):
    resets_at = window.get("resetsAt")

    if resets_at is None:
        return None

    seconds = max(0, int(resets_at - (time.time() if now is None else now)))
    days, remainder = divmod(seconds, 24 * 60 * 60)
    hours, remainder = divmod(remainder, 60 * 60)
    minutes = remainder // 60

    if days:
        return f"{days}d {hours}h"

    if hours:
        return f"{hours}h {minutes}m"

    if seconds and not minutes:
        return "<1m"

    return f"{minutes}m"


def remaining_percent(window):
    return max(0, min(100, 100 - int(window.get("usedPercent", 0))))


def format_output(payload, stale=False, mode="default"):
    windows = limit_windows(payload)
    parts = []

    for window in windows:
        label = f"{window_label(window)} "

        if len(windows) == 1 and window.get("windowDurationMins") == 7 * 24 * 60:
            label = ""

        parts.append(f"%{{F#ffffff}}{label}{remaining_percent(window)}%%{{F-}}")

    weekly = next((window for window in windows if window.get("windowDurationMins") == 7 * 24 * 60), None)

    if weekly is not None:
        countdown = reset_countdown(weekly)

        if countdown is not None:
            parts.append(f"%{{F#ffffff}}{countdown}%{{F-}}")

    if not parts:
        return "Codex no limits"

    icon = OPENAI_ICON

    if mode == "fast":
        icon += FAST_MODE_DOT

    parts.insert(0, icon)
    return " ".join(parts)


def read_cache():
    try:
        return json.loads(CACHE_PATH.read_text())
    except (OSError, ValueError):
        return None


def write_cache(payload):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = CACHE_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload))
    temporary.replace(CACHE_PATH)


def trigger_refresh():
    try:
        process_id = int(PID_PATH.read_text().strip())
        os.kill(process_id, signal.SIGUSR1)
        return 0
    except (OSError, ValueError):
        return 1


def main():
    last_payload = read_cache()
    mode = "default"
    fast_mode_expires_at = None
    stale = last_payload is not None
    results = queue.SimpleQueue()
    refresh = threading.Event()
    stopping = threading.Event()
    wake_reader, wake_writer = socket.socketpair()
    wake_reader.setblocking(False)
    wake_writer.setblocking(False)

    def ignore_signal(_signum, _frame):
        pass

    previous_handlers = {
        signum: signal.signal(signum, ignore_signal)
        for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1)
    }
    previous_wakeup_fd = signal.set_wakeup_fd(wake_writer.fileno())

    def fetch_worker():
        server = None

        try:
            while True:
                refresh.wait()
                refresh.clear()

                if stopping.is_set():
                    return

                try:
                    if server is None:
                        server = CodexAppServer()

                    payload = server.fetch_limits()
                    write_cache(payload)
                    results.put((payload, False))
                except (OSError, KeyError, RuntimeError, TimeoutError):
                    if server is not None:
                        server.close()
                        server = None

                    results.put((None, True))

                try:
                    wake_writer.send(b"\x00")
                except BlockingIOError:
                    pass
        finally:
            if server is not None:
                server.close()

    worker = threading.Thread(target=fetch_worker, daemon=True)
    PID_PATH.parent.mkdir(parents=True, exist_ok=True)
    PID_PATH.write_text(str(os.getpid()))
    worker.start()
    next_poll_at = time.monotonic()
    next_redraw_at = next_poll_at
    redraw = True

    try:
        while True:
            now = time.monotonic()

            if fast_mode_expires_at is not None and now >= fast_mode_expires_at:
                mode = "default"
                fast_mode_expires_at = None
                next_poll_at = now
                redraw = True

            while not results.empty():
                payload, stale = results.get()

                if payload is not None:
                    last_payload = payload

                redraw = True

            if redraw or now >= next_redraw_at:
                output = (
                    format_output(last_payload, stale=stale, mode=mode)
                    if last_payload
                    else "Codex unavailable"
                )
                print(output, flush=True)
                redraw = False
                next_redraw_at = now + 60

            if now >= next_poll_at:
                refresh.set()
                interval = FAST_POLL_SECONDS if mode == "fast" else NORMAL_POLL_SECONDS
                next_poll_at = now + interval

            deadline = min(next_poll_at, next_redraw_at)

            if fast_mode_expires_at is not None:
                deadline = min(deadline, fast_mode_expires_at)

            ready, _, _ = select.select(
                [wake_reader], [], [], max(0, deadline - time.monotonic())
            )

            if ready:
                for event in wake_reader.recv(4096):
                    if event in (signal.SIGTERM, signal.SIGINT):
                        return

                    if event == signal.SIGUSR1:
                        mode = "fast" if mode == "default" else "default"
                        fast_mode_expires_at = (
                            time.monotonic() + FAST_MODE_DURATION_SECONDS
                            if mode == "fast" else None
                        )
                        next_poll_at = time.monotonic()
                        redraw = True
    finally:
        stopping.set()
        refresh.set()
        worker.join(timeout=2 * TIMEOUT_SECONDS + 2)
        signal.set_wakeup_fd(previous_wakeup_fd)

        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)

        wake_reader.close()
        wake_writer.close()

        try:
            if int(PID_PATH.read_text().strip()) == os.getpid():
                PID_PATH.unlink()
        except (OSError, ValueError):
            pass


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--trigger":
        sys.exit(trigger_refresh())
    main()
