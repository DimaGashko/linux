#!/bin/bash

bat=$(bluetooth-battery-level)
if [[ -z "$bat" ]]; then
   echo ""
   exit 0
fi

color="#fff"
if (($bat < 20)); then
   color="#f00"
fi

echo "%{F$color}%{T2} %{T-}%{T1}$bat%%{F-}%{T-}"
