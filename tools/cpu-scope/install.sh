#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
python -c "import gi, cairo; gi.require_version('Gtk', '4.0'); gi.require_version('Adw', '1'); from gi.repository import Gtk, Adw" || {
    echo 'Install dependencies: sudo pacman -S python python-gobject python-cairo gtk4 libadwaita' >&2
    exit 1
}
app_dir="${XDG_DATA_HOME:-$HOME/.local/share}/cpu-scope/app"
mkdir -p "$app_dir" "$HOME/.local/bin" "${XDG_DATA_HOME:-$HOME/.local/share}/applications" "${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
install -m 644 app.py storage.py recorder.py stress_test.py "$app_dir/"
# Use Python to quote executable paths correctly for each file format.
python - "$app_dir" <<'PY'
from pathlib import Path
import os, shlex, sys
app = Path(sys.argv[1])
home = Path.home()
data = Path(os.environ.get('XDG_DATA_HOME', home / '.local/share'))
config = Path(os.environ.get('XDG_CONFIG_HOME', home / '.config'))
launcher = home / '.local/bin/cpu-scope'
launcher.write_text('#!/bin/sh\n'
                    '# Development flags run directly; normal launches belong to the user service.\n'
                    'if [ "$#" -gt 0 ]; then\n'
                    '    exec /usr/bin/python ' + shlex.quote(str(app / 'app.py')) + ' "$@"\n'
                    'fi\n'
                    '/usr/bin/systemctl --user import-environment DISPLAY XAUTHORITY WAYLAND_DISPLAY >/dev/null 2>&1 || :\n'
                    '/usr/bin/systemctl --user start cpu-scope-ui.service || exit $?\n'
                    '# i3 can keep an existing window behind another tab on its workspace.\n'
                    'if command -v i3-msg >/dev/null 2>&1; then\n'
                    '    i3-msg \'[title="^CPU Scope$"] focus\' >/dev/null 2>&1 || :\n'
                    'fi\n')
launcher.chmod(0o755)
# systemd specifiers and desktop field codes must be escaped separately.
unit_path = str(app / 'recorder.py').replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%')
app_unit_path = str(app / 'app.py').replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%')
(config / 'systemd/user/cpu-scope-recorder.service').write_text(f'''[Unit]
Description=CPU Scope frequency and utilization history

[Service]
Type=simple
ExecStart=/usr/bin/python "{unit_path}"
Restart=on-failure
RestartSec=5
Nice=10
UMask=0077
NoNewPrivileges=true

[Install]
WantedBy=default.target
''')
(config / 'systemd/user/cpu-scope-ui.service').write_text(f'''[Unit]
Description=CPU Scope window
StartLimitIntervalSec=60
StartLimitBurst=5

[Service]
Type=exec
ExecStart=/usr/bin/python "{app_unit_path}"
Restart=on-failure
RestartSec=3
StandardOutput=journal
StandardError=journal

''')
exec_path = str(launcher).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%')
(data / 'applications/io.local.CpuScope.desktop').write_text(f'''[Desktop Entry]
Type=Application
Name=CPU Scope
Comment=CPU frequency, utilization and persistent history
Exec="{exec_path}"
Icon=utilities-system-monitor
Terminal=false
Categories=System;Monitor;
StartupNotify=true
''')
PY
systemctl --user daemon-reload
systemctl --user enable cpu-scope-recorder.service
systemctl --user restart cpu-scope-recorder.service
if command -v update-desktop-database >/dev/null; then
    update-desktop-database "${XDG_DATA_HOME:-$HOME/.local/share}/applications"
fi
printf 'Installed. Launch: %s/.local/bin/cpu-scope\n' "$HOME"
