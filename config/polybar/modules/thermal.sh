#!/bin/bash

profile=$(cat /tmp/thermal-profile)
icon=""

if [[ $profile == "Balanced" ]]; then
   icon=""
elif [[ $profile == "Quiet" ]]; then
   icon=""
elif [[ $profile == "Cool Bottom" ]]; then
   icon=""
elif [[ $profile == "Performance" ]]; then
   icon=""
fi

if [[ $profile == "Cool Bottom" ]]; then
   profile="Cool"
fi

echo $icon $profile