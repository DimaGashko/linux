set $mod Mod4

# TODO: low battery notification
# TODO: full battery notification
# TODO: move focus only inside current output
# TODO: improve lock/logout/shutdown system
 
font pango:unifont 10

floating_modifier $mod

bindsym $mod+Shift+c reload
bindsym $mod+Shift+r restart

# Do not activate window on a title bar click 
bindsym button1 nop