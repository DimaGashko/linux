# i3 keeps all normal bindings active while the IPC helper accumulates digits.
bindsym $mod+0 nop workspace-input switch 0
bindsym --release $mod+0 nop workspace-input release 0
bindsym $mod+Shift+0 nop workspace-input move 0
bindsym --release $mod+Shift+0 nop workspace-input release 0

bindsym $mod+1 nop workspace-input switch 1
bindsym --release $mod+1 nop workspace-input release 1
bindsym $mod+Shift+1 nop workspace-input move 1
bindsym --release $mod+Shift+1 nop workspace-input release 1

bindsym $mod+2 nop workspace-input switch 2
bindsym --release $mod+2 nop workspace-input release 2
bindsym $mod+Shift+2 nop workspace-input move 2
bindsym --release $mod+Shift+2 nop workspace-input release 2

bindsym $mod+3 nop workspace-input switch 3
bindsym --release $mod+3 nop workspace-input release 3
bindsym $mod+Shift+3 nop workspace-input move 3
bindsym --release $mod+Shift+3 nop workspace-input release 3

bindsym $mod+4 nop workspace-input switch 4
bindsym --release $mod+4 nop workspace-input release 4
bindsym $mod+Shift+4 nop workspace-input move 4
bindsym --release $mod+Shift+4 nop workspace-input release 4

bindsym $mod+5 nop workspace-input switch 5
bindsym --release $mod+5 nop workspace-input release 5
bindsym $mod+Shift+5 nop workspace-input move 5
bindsym --release $mod+Shift+5 nop workspace-input release 5

bindsym $mod+6 nop workspace-input switch 6
bindsym --release $mod+6 nop workspace-input release 6
bindsym $mod+Shift+6 nop workspace-input move 6
bindsym --release $mod+Shift+6 nop workspace-input release 6

bindsym $mod+7 nop workspace-input switch 7
bindsym --release $mod+7 nop workspace-input release 7
bindsym $mod+Shift+7 nop workspace-input move 7
bindsym --release $mod+Shift+7 nop workspace-input release 7

bindsym $mod+8 nop workspace-input switch 8
bindsym --release $mod+8 nop workspace-input release 8
bindsym $mod+Shift+8 nop workspace-input move 8
bindsym --release $mod+Shift+8 nop workspace-input release 8

bindsym $mod+9 nop workspace-input switch 9
bindsym --release $mod+9 nop workspace-input release 9
bindsym $mod+Shift+9 nop workspace-input move 9
bindsym --release $mod+Shift+9 nop workspace-input release 9

bindsym $mod+grave nop workspace-input switch grave
bindsym --release $mod+grave nop workspace-input release grave
bindsym $mod+Shift+grave nop workspace-input move grave
bindsym --release $mod+Shift+grave nop workspace-input release grave

bindsym $mod+minus workspace --no-auto-back-and-forth "A"
bindsym $mod+Shift+minus move container to workspace "A"; workspace --no-auto-back-and-forth "A"
bindsym $mod+Ctrl+minus move container to workspace "A"; workspace --no-auto-back-and-forth "A"

bindsym $mod+equal workspace --no-auto-back-and-forth "B"
bindsym $mod+Shift+equal move container to workspace "B"; workspace --no-auto-back-and-forth "B"
bindsym $mod+Ctrl+equal move container to workspace "B"; workspace --no-auto-back-and-forth "B"

bindsym $mod+BackSpace workspace --no-auto-back-and-forth "C"
bindsym $mod+Shift+BackSpace move container to workspace "C"; workspace --no-auto-back-and-forth "C"
bindsym $mod+Ctrl+BackSpace move container to workspace "C"; workspace --no-auto-back-and-forth "C"

bindsym $mod+Home workspace --no-auto-back-and-forth "124"
bindsym $mod+Shift+Home move container to workspace "124"; workspace --no-auto-back-and-forth "124"
bindsym $mod+Ctrl+Home move container to workspace "124"; workspace --no-auto-back-and-forth "124"

bindsym $mod+plus workspace --no-auto-back-and-forth "B"
bindsym $mod+Shift+plus move container to workspace "B"; workspace --no-auto-back-and-forth "B"
bindsym $mod+Ctrl+plus move container to workspace "B"; workspace --no-auto-back-and-forth "B"

bindsym $mod+Ctrl+grave move container to workspace "0"; workspace --no-auto-back-and-forth "0"
