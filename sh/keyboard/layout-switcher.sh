#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cache_dir="${XDG_CACHE_HOME:-$HOME/.cache}/keyboard-layout-switcher"
binary="$cache_dir/layout-switcher"
mkdir -p "$cache_dir"

if [[ ! -x $binary || "$script_dir/layout-switcher.c" -nt $binary ]]; then
    temporary=$(mktemp "$cache_dir/build.XXXXXX")
    trap 'rm -f "$temporary"' EXIT
    cc -std=c11 -O2 -Wall -Wextra -Werror "$script_dir/layout-switcher.c" -lX11 -o "$temporary"
    mv -f "$temporary" "$binary"
    trap - EXIT
fi

if (($#)); then
    exec "$binary" "$@"
fi

display_key=${DISPLAY//[^[:alnum:]]/_}
exec 9>"${XDG_RUNTIME_DIR:-$cache_dir}/keyboard-layout-switcher-$display_key.lock"
flock -n 9 || exit 0

setxkbmap -model pc105 -layout us,ru,ua -option ''
exec "$binary"
