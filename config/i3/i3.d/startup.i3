exec_always --no-startup-id feh --bg-scale ~/Pictures/wallpapers/bg2.jpg
exec_always --no-startup-id setxkbmap -model pc105 -option 'grp:win_space_toggle'
exec_always --no-startup-id setxkbmap -layout us,ru

exec_always --no-startup-id spd-say "Nice to meet you, my friend"
exec_always --no-startup-id ~/linux/config/polybar/launch.sh

exec --no-startup-id compton -f -D 6
#exec --no-startup-id ~/i3/i3-battery-popup/i3-battery-popup -L 20 -l 10 -t 2m -n -s ~/i3/i3-battery-popup/sounds/0.wav -i ~/i3/i3-battery-popup/icons/0.png
