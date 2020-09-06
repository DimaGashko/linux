set $wsa "121"
set $wsb "122"

bindsym $mod+minus workspace $wsa
bindsym $mod+plus workspace $wsb

bindsym $mod+Shift+minus move container to workspace $wsa
bindsym $mod+Shift+plus move container to workspace $wsb

bindsym $mod+Ctrl+minus move container to workspace number $wsa; workspace $wsa
bindsym $mod+Ctrl+plus move container to workspace number $wsb; workspace $wsb