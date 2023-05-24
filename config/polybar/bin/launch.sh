#!/usr/bin/env bash

# Kill already running instances but only inside the current X11 session
for id in $(xwininfo -root -tree | grep 'polybar-' | awk '{print $1}'); do
   xprop -id $id _NET_WM_PID | awk '{print $3}' | xargs kill
done

polybar eDP-1 >> "/var/log/userlog/polybar.eDP-1.log" 2>&1 &
polybar DP-3 >> "/var/log/userlog/polybar.DP-3.log" 2>&1 & 
polybar DP-4 >> "/var/log/userlog/polybar.DP-4.log" 2>&1 &
