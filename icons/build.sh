#!/usr/bin/env bash
set -euo pipefail

icon_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

if ! command -v inkscape >/dev/null; then
    echo 'Inkscape is required to turn SVG strokes into font outlines.' >&2
    exit 1
fi

if [[ ! -x "$icon_root/.venv/bin/python" ]]; then
    python3 -m venv "$icon_root/.venv"
fi

"$icon_root/.venv/bin/python" -m pip install --disable-pip-version-check -r "$icon_root/requirements.txt"
"$icon_root/.venv/bin/python" "$icon_root/build.py"
