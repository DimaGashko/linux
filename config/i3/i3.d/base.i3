set $mod Mod4

set $exec exec --no-startup-id
set $exec_always exec_always --no-startup-id

set $gen ~/config/i3/gen-i3.sh

# TODO: low battery notification
# TODO: full battery notification
# TODO: move focus only inside current output
# TODO: improve lock/logout/shutdown system
 
font pango:unifont 10

floating_modifier $mod

# Do not activate window on a title bar click 
bindsym button1 nop

bindsym $mod+Shift+c $exec $gen && i3-msg reload
bindsym $mod+Shift+r $exec $gen && i3-msg restart

# Just 12 groups of workspaces with 10 workspaces on each one
bindsym Ctrl+1 $exec $gen 0 && i3-msg reload
bindsym Ctrl+2 $exec $gen 1 && i3-msg reload
bindsym Ctrl+3 $exec $gen 2 && i3-msg reload
bindsym Ctrl+4 $exec $gen 3 && i3-msg reload
bindsym Ctrl+5 $exec $gen 4 && i3-msg reload
bindsym Ctrl+6 $exec $gen 5 && i3-msg reload
bindsym Ctrl+7 $exec $gen 6 && i3-msg reload
bindsym Ctrl+8 $exec $gen 7 && i3-msg reload
bindsym Ctrl+9 $exec $gen 8 && i3-msg reload
bindsym Mod1+Ctrl+0 $exec $gen 9 && i3-msg reload
bindsym Mod1+Ctrl+minus $exec $gen 10 && i3-msg reload
bindsym Mod1+Ctrl+plus $exec $gen 11 && i3-msg reload

# Plus some common workspaces
bindsym $mod+grave workspace "0"
bindsym $mod+minus workspace "121"
bindsym $mod+plus workspace "122"
bindsym $mod+BackSpace workspace "123"
bindsym $mod+Home workspace "124"

bindsym $mod+Shift+grave move container to workspace "0"
bindsym $mod+Shift+minus move container to workspace "121"
bindsym $mod+Shift+plus move container to workspace "122"
bindsym $mod+Shift+BackSpace move container to workspace "123"
bindsym $mod+Shift+Home move container to workspace "124"

bindsym $mod+Ctrl+grave move container to workspace number "0; workspace "0"
bindsym $mod+Ctrl+minus move container to workspace number "121"; workspace "121"
bindsym $mod+Ctrl+plus move container to workspace number "122"; workspace "122"
bindsym $mod+Ctrl+BackSpace move container to workspace number "123"; workspace "123"
bindsym $mod+Ctrl+Home move container to workspace number "124"; workspace "124"
