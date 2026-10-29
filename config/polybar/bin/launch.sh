#!/usr/bin/env bash
set -euo pipefail

config_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
log_dir="${XDG_CACHE_HOME:-$HOME/.cache}/polybar"
display_key=${DISPLAY//[^[:alnum:]]/_}
mkdir -p "$log_dir"

# Serialize restarts, but do not let child bars inherit the lock.
exec 9>"$log_dir/launch-$display_key.lock"
flock 9

mapfile -t monitors < <(polybar --list-monitors | cut -d: -f1)
bars=()

for monitor in "${monitors[@]}"; do
    if grep -qFx "[bar/$monitor]" "$config_dir/config.ini"; then
        bars+=("$monitor")
    fi
done

if ((${#bars[@]} == 0)); then
    echo 'No configured Polybar monitor is connected.' >&2
    exit 1
fi

# Scope termination to Polybar windows in this X11 session, not every login.
mapfile -t windows < <(xwininfo -root -tree | awk '/"polybar-/ {print $1}')
pids=()

for window in "${windows[@]}"; do
    pid=$(xprop -id "$window" _NET_WM_PID 2>/dev/null | awk '/= [0-9]+$/ {print $NF}') || continue

    if [[ $pid =~ ^[0-9]+$ && $(cat "/proc/$pid/comm" 2>/dev/null) == polybar ]]; then
        pids+=("$pid")
        kill -TERM "$pid" 2>/dev/null || true
    fi
done

# Wait for old bars to release the tray selection before starting replacements.
for ((attempt = 0; attempt < 50; attempt++)); do
    running=false

    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            running=true
        fi
    done

    if [[ $running == false ]]; then
        break
    fi

    sleep 0.1
done

for pid in "${pids[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
        echo "Polybar $pid did not stop; keeping the restart pending." >&2
        exit 1
    fi
done

for bar in "${bars[@]}"; do
    nohup setsid polybar --config="$config_dir/config.ini" "$bar" \
        </dev/null >>"$log_dir/$bar.log" 2>&1 9>&- &
done
