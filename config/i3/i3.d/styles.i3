# colors
set $bg-color 	          #2f343f
set $inactive-bg-color   #2f343f
set $text-color          #ff0000
set $inactive-text-color #ff0000
set $urgent-bg-color     #E53935

# window colors
#                        border              background         text                  indicator
client.focused           #607D8B             #607D8B            $text-color           #607D8B
client.unfocused         #263238             #263238 $inactive-text-color  #607D8B
client.focused_inactive  $inactive-bg-color  $inactive-bg-color $inactive-text-color  #607D8B
client.urgent            $urgent-bg-color    $urgent-bg-color   $text-color           #607D8B

# hide tabs (in tab mode) (as much as possible)
for_window [all] title_format " "
font pango:unifont 0.5

# Do not activate window on a title bar click 
bindsym button1 nop

focus_on_window_activation focus
floating_minimum_size 300 x 50
floating_maximum_size -1 x -1
default_floating_border pixel 1
default_border pixel 0
hide_edge_borders both

gaps inner 6
smart_gaps on
