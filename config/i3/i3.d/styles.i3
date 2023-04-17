# colors
set $bg-color 	          #2f343f
set $inactive-bg-color   #2f343f
set $text-color          #f3f4f5
set $inactive-text-color #676E7D
set $urgent-bg-color     #E53935

# window colors
#                        border              background         text                  indicator
client.focused           #3f454f             $bg-color          $text-color           #607D8B
client.unfocused         $inactive-bg-color  $inactive-bg-color $inactive-text-color  #607D8B
client.focused_inactive  $inactive-bg-color  $inactive-bg-color $inactive-text-color  #607D8B
client.urgent            $urgent-bg-color    $urgent-bg-color   $text-color           #607D8B

gaps inner 5
smart_gaps on