#!/usr/bin/env bash
set -euo pipefail
systemctl --user disable --now cpu-scope-ui.service || true
systemctl --user disable --now cpu-scope-recorder.service
rm -f -- "${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/cpu-scope-ui.service" "${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/cpu-scope-recorder.service"
systemctl --user daemon-reload
rm -f -- "$HOME/.local/bin/cpu-scope" "${XDG_DATA_HOME:-$HOME/.local/share}/applications/io.local.CpuScope.desktop"
rm -f -- "${XDG_DATA_HOME:-$HOME/.local/share}/cpu-scope/app/"{app.py,storage.py,recorder.py,stress_test.py}
echo 'Uninstalled. Your recorded history has been preserved.'
