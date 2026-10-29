#!/usr/bin/env bash
set -euo pipefail

icon_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
font_dir="${XDG_DATA_HOME:-$HOME/.local/share}/fonts/custom-system-icons"

"$icon_root/build.sh"
install -Dm644 "$icon_root/dist/CustomSystemIcons.ttf" "$font_dir/CustomSystemIcons.ttf"
fc-cache -f "$font_dir"
fc-match 'Custom System Icons'
printf 'Installed font in %s\n' "$font_dir"
