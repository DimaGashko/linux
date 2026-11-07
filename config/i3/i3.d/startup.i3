$exec ~/linux/sh/bgShow.sh 3600

$exec xset s off +dpms dpms 900 900 900

$exec xscreensaver --no-splash

$exec_always picom

$exec_always ~/linux/sh/keyboard/layout-switcher.sh

$exec_always ~/config/i3/sh/workspace-input.py --timeout-ms 300

$exec_always ~/config/polybar/bin/launch.sh

$exec_always nm-applet
