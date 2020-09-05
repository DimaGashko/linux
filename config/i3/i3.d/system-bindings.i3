bindsym $mod+Shift+e exec "i3-nagbar -t warning -m 'Do you really want to exit i3? This will end your X session.' -B 'Yes, exit i3' 'i3-msg exit'"

# Pulse Audio controls
bindsym XF86AudioRaiseVolume exec --no-startup-id amixer -D pulse sset Master 5%+
bindsym XF86AudioLowerVolume exec --no-startup-id amixer -D pulse sset Master 5%-
bindsym XF86AudioMute exec --no-startup-id amixer -D pulse sset Master toggle

bindsym Ctrl+XF86AudioRaiseVolume exec --no-startup-id pactl set-sink-volume @DEFAULT_SINK@ +5%
bindsym Ctrl+XF86AudioLowerVolume exec --no-startup-id pactl set-sink-volume @DEFAULT_SINK@ -5%

# Sreen brightness controls
bindsym XF86MonBrightnessUp exec xbacklight -inc 10
bindsym XF86MonBrightnessDown exec xbacklight -dec 10

bindsym Shift+XF86MonBrightnessUp exec xbacklight -inc 2
bindsym Shift+XF86MonBrightnessDown exec xbacklight -dec 2

bindsym Ctrl+XF86MonBrightnessUp exec xbacklight -set 100
bindsym Ctrl+XF86MonBrightnessDown exec xbacklight -set 0

# reading mode
bindsym $mod+XF86MonBrightnessUp exec --no-startup-id sct 4500 && echo 1 > /tmp/night
bindsym $mod+XF86MonBrightnessDown exec --no-startup-id sct && echo 0 > /tmp/night

# Media player controls
bindsym XF86AudioNext exec playerctl next
bindsym XF86AudioPrev exec playerctl previous
bindsym XF86AudioPlay exec playerctl play
bindsym XF86AudioPause exec playerctl pause
bindsym $mod+m exec playerctl play-pause

# PrtScn
bindsym Print exec --no-startup-id flameshot gui

# bindsym --release $mod+r exec --no-startup-id xdotool key --clearmodifiers F5