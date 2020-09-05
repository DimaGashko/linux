set $wsa "a"
set $wsb "b"

bindsym $mod+- workspace $wsa
bindsym $mod++ workspace $wsb

bindsym $mod+Shift+- move container to workspace $wsa
bindsym $mod+Shift++ move container to workspace $wsb

bindsym $mod+Ctrl+- move container to workspace number $wsa; workspace $wsa
bindsym $mod+Ctrl++ move container to workspace number $wsb; workspace $wsb
