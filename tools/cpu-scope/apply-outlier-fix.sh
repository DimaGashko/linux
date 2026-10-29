#!/usr/bin/env bash
# Install frequency validation and repair recent history with a SQLite backup.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
app_dir="${XDG_DATA_HOME:-$HOME/.local/share}/cpu-scope/app"
systemctl --user stop cpu-scope-recorder.service
trap 'systemctl --user start cpu-scope-recorder.service' EXIT
python repair_history.py
install -m 644 storage.py recorder.py "$app_dir/"
systemctl --user start cpu-scope-recorder.service
trap - EXIT
