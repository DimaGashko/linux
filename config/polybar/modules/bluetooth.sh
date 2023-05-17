#!/bin/bash

if ! bluetoothctl info | grep -q "Connected: yes"; then
   echo ""
   exit 0
fi

bat=$(~/linux/sh/bluetooth-battery-level.sh)
if [[ -z "$bat" ]]; then
   echo "0"
   exit 0
fi

color="#fff"
if (($bat < 5)); then
   color="#f00"
fi

echo "%{F$color}%{T2} %{T-}%{T1}$bat%%{F-}%{T-}"
