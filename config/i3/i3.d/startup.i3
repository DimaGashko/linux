$exec ~/linux/sh/thermal/update-thermal.sh
$exec ~/linux/sh/bgShow.sh 3600

$exec_always picom

$exec_always setxkbmap -layout us,ru -model pc105 -option 'grp:win_space_toggle'

$exec_always ~/config/polybar/bin/launch.sh

$exec_always nm-applet
