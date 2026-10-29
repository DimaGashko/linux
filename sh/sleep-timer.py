#!/usr/bin/env python3

import argparse
import math
import re
import shutil
import subprocess
import sys
import time
from decimal import Decimal


UNIT = "linux-sleep"
TIMER_PATH = "/org/freedesktop/systemd1/unit/linux_2dsleep_2etimer"


def cancel():
    result = subprocess.run(
        ["systemctl", "--user", "stop", f"{UNIT}.timer", f"{UNIT}.service"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    if result.returncode not in (0, 5):
        raise RuntimeError(result.stderr.strip())


def start(duration):
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)([smh]?)", duration)

    if match is None:
        raise ValueError("Use seconds, minutes or hours, e.g. 30s, 2.5m, 1.5h")

    seconds = Decimal(match[1]) * {"": 1, "s": 1, "m": 60, "h": 3600}[match[2]]
    systemctl = shutil.which("systemctl")

    if systemctl is None:
        raise RuntimeError("systemctl not found")

    cancel()

    if seconds == 0:
        subprocess.run([systemctl, "suspend"], check=True)
        return

    subprocess.run(
        [
            "systemd-run",
            "--user",
            "--quiet",
            "--collect",
            f"--unit={UNIT}",
            f"--on-active={seconds:f}s",
            "--timer-property=AccuracySec=1s",
            "--timer-property=RemainAfterElapse=no",
            systemctl,
            "suspend",
        ],
        check=True,
        timeout=5,
    )


def format_remaining(seconds):
    if seconds < 90:
        return f"{seconds}s"

    hours, minutes = divmod(math.ceil(seconds / 60), 60)
    return f"{hours}:{minutes:02d}"


def status():
    result = subprocess.run(
        [
            "busctl",
            "--user",
            "--timeout=2",
            "get-property",
            "org.freedesktop.systemd1",
            TIMER_PATH,
            "org.freedesktop.systemd1.Timer",
            "NextElapseUSecMonotonic",
        ],
        capture_output=True,
        text=True,
        timeout=3,
    )

    if result.returncode != 0:
        return

    signature, deadline = result.stdout.split()

    if signature != "t":
        return

    deadline = int(deadline)

    if deadline in (0, 2**64 - 1):
        return

    remaining = math.ceil(deadline / 1_000_000 - time.monotonic())

    if remaining > 0:
        return f"Sleep {format_remaining(remaining)}"


def main():
    parser = argparse.ArgumentParser(description="Schedule sleep and show its countdown")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("start").add_argument("duration")
    commands.add_parser("cancel")
    commands.add_parser("status")
    args = parser.parse_args()

    try:
        if args.command == "start":
            start(args.duration)
        elif args.command == "cancel":
            cancel()
        else:
            print(status() or "")
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(error, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
