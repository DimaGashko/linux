set $mod Mod4
set $gen ~/config/i3/gen-i3.sh

# TODO: low battery notification
# TODO: full battery notification
# TODO: move focus only inside current output
# TODO: improve lock/logout/shutdown system
 
font pango:unifont 10

floating_modifier $mod

# Do not activate window on a title bar click 
bindsym button1 nop

bindsym $mod+Shift+c exec $gen && i3-msg reload
bindsym $mod+Shift+r exec $gen && i3-msg restart

bindsym $mod+Mod1+1 exec $gen 0 && i3-msg reload
bindsym $mod+Mod1+2 exec $gen 1 && i3-msg reload
bindsym $mod+Mod1+3 exec $gen 2 && i3-msg reload
bindsym $mod+Mod1+4 exec $gen 3 && i3-msg reload
bindsym $mod+Mod1+5 exec $gen 4 && i3-msg reload
bindsym $mod+Mod1+6 exec $gen 5 && i3-msg reload
bindsym $mod+Mod1+7 exec $gen 6 && i3-msg reload
bindsym $mod+Mod1+8 exec $gen 7 && i3-msg reload
bindsym $mod+Mod1+9 exec $gen 8 && i3-msg reload
bindsym $mod+Mod1+0 exec $gen 9 && i3-msg reload