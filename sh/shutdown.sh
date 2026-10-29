#!/bin/bash

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

options="Sleep\0icon\x1f<span color='#fff'></span>
Hibernate\0icon\x1f<span color='#fff'></span>
Power off\0icon\x1f<span color='#fff'></span>
Reboot\0icon\x1f<span color='#fff'></span>
Exit i3\0icon\x1f<span color='#fff'></span>
Cancel\0icon\x1f<span color='#fff'>󱎘</span>"

len=$(echo "$options" | wc -l)
choice=$(echo -en "$options" | rofi -dmenu -p ">" -show-icons -i -l $len)

case $choice in
"Sleep")
   if ! duration=$(rofi-in "Sleep in"); then
      exit 0
   fi

   if [[ "$duration" == "-1" ]]; then
      "$script_dir/sleep-timer.py" cancel
   else
      "$script_dir/sleep-timer.py" start "${duration:-0}"
   fi
   ;;
"Power off")
   if [[ $(confirm) != "YES" ]]; then
      exit 0
   fi

   echo "Power off"
   systemctl poweroff
   ;;
"Reboot")
   if [[ $(confirm) != "YES" ]]; then
      exit 0
   fi

   echo "Reboot"
   systemctl reboot
   ;;
"Hibernate")
   if [[ $(confirm) != "YES" ]]; then
      exit 0
   fi

   echo "Hibernate"
   systemctl hibernate
   ;;
"Exit i3")
   if [[ $(confirm) != "YES" ]]; then
      exit 0
   fi

   echo "Exit i3"
   i3-msg exit
   ;;
*)
   echo "Canceled"
   ;;
esac
