#!/bin/bash

profile=$(~/linux/sh/thermal/update-thermal.sh) || exit 1
icon=""

if [[ $profile == "Balanced" ]]; then
   icon=""
elif [[ $profile == "Quiet" ]]; then
   icon=""
elif [[ $profile == "Cool" ]]; then
   icon=""
elif [[ $profile == "Performance" ]]; then
   icon=""
fi

printf '%%{T2}%s%%{T3} %s\n' "$icon" "$profile"
