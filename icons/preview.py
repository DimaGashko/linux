#!/usr/bin/env python3
"""Render every installed glyph and both usage states with Polybar in Xvfb."""

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main():
    sys.dont_write_bytecode = True
    entries = json.loads((ROOT / "manifest.json").read_text())
    glyphs = " ".join(chr(int(entry["codepoint"], 16)) for entry in entries)
    module = ROOT.parent / "config/polybar/modules/codex-usage.py"
    spec = importlib.util.spec_from_file_location("codex_usage", module)
    usage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(usage)
    payload = {"rateLimits": {"primary": {"usedPercent": 0, "windowDurationMins": 300}}}
    default = usage.format_output(payload)
    fast = usage.format_output(payload, mode="fast")
    output = ROOT / "dist/polybar-preview.png"
    output.unlink(missing_ok=True)

    config = f"""[bar/preview]
monitor = screen
dpi = 96
width = 1250
height = 24
background = #000000
foreground = #ffffff
override-redirect = true
padding-left = 8px
module-margin = 16px
font-0 = DroidSansMono Nerd Font:size=10:style=Regular;3
font-1 = Custom System Icons:size=13.5:dpi=96;3
font-2 = NotoSans Nerd Font:size=10:style=ExtraBold;3
modules-left = icons states

[module/icons]
type = custom/text
format = %{{T2}}{glyphs}%{{T-}}

[module/states]
type = custom/text
format = %{{T1}}Normal: {default}   %{{T1}}Fast: {fast}
"""

    with tempfile.TemporaryDirectory(prefix="panel-icon-preview-") as temporary:
        config_path = Path(temporary) / "config.ini"
        config_path.write_text(config)
        result = subprocess.run(
            [
                "xvfb-run", "-a", "-s", "-screen 0 1250x100x24",
                "timeout", "5s", "polybar", "-c", str(config_path),
                "-p", str(output), "preview",
            ],
            capture_output=True, text=True, timeout=15,
        )

    log = result.stdout + result.stderr
    (ROOT / "build/polybar-preview.log").write_text(log)

    if result.returncode not in (0, 124) or not output.is_file():
        raise RuntimeError(f"Polybar preview failed:\n{log}")

    if "Dropping unmatched character" in log or "error:" in log:
        raise RuntimeError(f"Polybar rendering error:\n{log}")

    print(f"Rendered {len(entries)} glyphs and normal/fast states: {output}")


if __name__ == "__main__":
    main()
