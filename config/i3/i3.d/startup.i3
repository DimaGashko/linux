$exec_always feh ~/images/bg/* --bg-scale --randomize  --no-fehbg 

$exec_always setxkbmap -model pc105 -option 'grp:win_space_toggle'
$exec_always setxkbmap -layout us,ru

$exec_always ~/linux/config/polybar/launch.sh

$exec_always picom --experimental-backends
