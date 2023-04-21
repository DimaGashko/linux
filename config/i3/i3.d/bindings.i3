bindsym $mod+Shift+e $exec "~/linux/sh/shutdown.sh"

bindsym $mod+Return $exec alacritty
bindsym $mod+Shift+Return $exec "alacritty --class AlacrittyFloating"

bindsym $mod+Shift+q kill

bindsym $mod+p $exec rofi -show drun
bindsym $mod+Shift+p $exec rofi -show window

bindsym $mod+b $exec bluetoothctl connect 64:03:7F:DE:AC:3E
bindsym $mod+Shift+b $exec bluetoothctl disconnect 64:03:7F:DE:AC:3E

bindsym $mod+z $exec ~/linux/sh/toggle-timezones.sh

bindsym $mod+h focus left
bindsym $mod+j focus down
bindsym $mod+k focus up
bindsym $mod+l focus right

bindsym $mod+Shift+h move left
bindsym $mod+Shift+j move down
bindsym $mod+Shift+k move up
bindsym $mod+Shift+l move right

bindsym $mod+braceleft split h
bindsym $mod+braceright split v

bindsym $mod+f fullscreen toggle

bindsym $mod+s layout stacking
bindsym $mod+w layout tabbed
bindsym $mod+e layout toggle split

bindsym $mod+y focus parent
bindsym $mod+Shift+y focus child

bindsym $mod+n floating toggle
bindsym $mod+Shift+n focus mode_toggle

bindsym $mod+0x2c move scratchpad
bindsym $mod+Shift+less scratchpad show

bindsym $mod+Left resize shrink width 100px or 10 ppt
bindsym $mod+Down resize grow height 100px or 10 ppt
bindsym $mod+Up resize shrink height 100px or 10 ppt
bindsym $mod+Right resize grow width 100px or 10 ppt

bindsym $mod+Shift+Left resize shrink width 1px
bindsym $mod+Shift+Down resize grow height 1px
bindsym $mod+Shift+Up resize shrink height 1px
bindsym $mod+Shift+Right resize grow width 1px

bindsym $mod+Prior resize grow width 100px or 10 ppt; resize grow height 100px or 10 ppt
bindsym $mod+Next resize shrink width 100px or 10 ppt; resize shrink height 100px or 10 ppt

bindsym $mod+u [urgent=latest] focus

bindsym $mod+Tab workspace back_and_forth
bindsym Mod1+Left workspace prev
bindsym Mod1+Right workspace next

bindsym $mod+Ctrl+Left move container to workspace prev; workspace prev
bindsym $mod+Ctrl+Right move container to workspace next; workspace next

bindsym Mod1+d $exec xrandr --output HDMI1 --auto --left-of eDP1
bindsym Mod1+f $exec xrandr --output DP1 --auto --right-of eDP1 
bindsym Mod1+Shift+d $exec xrandr --auto

bindsym $mod+d move workspace to output right

bindsym $mod+o $exec ~/config/polybar/bin/launch.sh

bindsym $mod+Ctrl+b $exec feh ~/linux/img/bg-images/* --bg-scale --randomize --no-fehbg

bindsym $mod+t $exec "setxkbmap -layout us,ru -model pc105 -option 'grp:win_space_toggle'"
bindsym $mod++Ctrl+t $exec "setxkbmap -layout us,ua -model pc105 -option 'grp:win_space_toggle'"
