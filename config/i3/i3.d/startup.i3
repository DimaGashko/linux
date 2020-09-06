exec_always --no-startup-id feh ~/images/bg/* --bg-scale --randomize  --no-fehbg 

exec_always --no-startup-id setxkbmap -model pc105 -option 'grp:win_space_toggle'
exec_always --no-startup-id setxkbmap -layout us,ru

exec_always --no-startup-id ~/linux/config/polybar/launch.sh

exec_always --no-startup-id picom --experimental-backends
