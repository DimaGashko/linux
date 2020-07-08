#!/usr/bin/env bash

killall -q polybar

echo "---" | tee -a /tmp/polybar-primary.log /tmp/polybar-secondary.log
polybar primary &
polybar secondary &

echo "Bars launched..."