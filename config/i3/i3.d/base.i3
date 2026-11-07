set $mod Mod4

# Double Fn
set $fn XF86Launch1

set $exec exec --no-startup-id
set $exec_always exec_always --no-startup-id

set $gen ~/config/i3/gen-i3.sh

# TODO: low battery notification
# TODO: full battery notification
# TODO: move focus only inside current output
# TODO: improve lock/logout/shutdown system

floating_modifier $mod

bindsym $mod+Shift+c $exec $gen && i3-msg reload
bindsym $mod+Shift+r $exec $gen && i3-msg restart
