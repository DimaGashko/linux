#!/usr/bin/env bash

killall -q polybar

echo "---" | tee -a /tmp/polybar-eDP1.log /tmp/polybar-HDMI1.log /tmp/polybar-DP1
polybar eDP1 &
polybar HDMI1 &
polybar DP1 &

echo "Bars launched..."