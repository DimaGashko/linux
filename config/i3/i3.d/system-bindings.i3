
# Pulse Audio controls
bindsym XF86AudioRaiseVolume $exec amixer -D pulse sset Master 5%+
bindsym XF86AudioLowerVolume $exec amixer -D pulse sset Master 5%-
bindsym XF86AudioMute $exec amixer -D pulse sset Master toggle

bindsym Ctrl+XF86AudioRaiseVolume $exec pactl set-sink-volume @DEFAULT_SINK@ +5%
bindsym Ctrl+XF86AudioLowerVolume $exec pactl set-sink-volume @DEFAULT_SINK@ -5%

# Screen brightness controls
bindsym XF86MonBrightnessUp $exec xbacklight -inc 10 -fps 60
bindsym XF86MonBrightnessDown $exec xbacklight -dec 10 -fps 60

bindsym Ctrl+XF86MonBrightnessUp $exec xbacklight -set 60 -fps 60
bindsym Ctrl+XF86MonBrightnessDown $exec xbacklight -set 0 -fps 60

bindsym Shift+XF86MonBrightnessUp $exec xbacklight -inc 2
bindsym Shift+XF86MonBrightnessDown $exec xbacklight -dec 2

# bindsym $mod+XF86MonBrightnessUp $exec sct 4500 && echo 1 > /tmp/night
# bindsym $mod+XF86MonBrightnessDown $exec sct && echo 0 > /tmp/night

bindsym XF86AudioToggle $exec playerctl play

# Media player controls
bindsym XF86AudioNext $exec playerctl next
bindsym XF86AudioPrev $exec playerctl previous
bindsym XF86AudioPlay $exec playerctl play
bindsym XF86AudioPause $exec playerctl pause
bindsym $mod+m $exec playerctl play-pause

# PrtScn
bindsym Print $exec flameshot gui