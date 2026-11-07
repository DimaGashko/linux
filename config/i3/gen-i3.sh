#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
temporary=$(mktemp .i3.config.XXXXXX)
trap 'rm -f "$temporary"' EXIT

for file in i3.d/*.i3; do
    printf '# - - - %s - - -\n' "$file"
    cat "$file"
    printf '\n\n'
done > "$temporary"

i3 -C -c "$temporary"
mv -f "$temporary" i3.config
