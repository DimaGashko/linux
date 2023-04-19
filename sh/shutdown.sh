#!/bin/bash

options="Cancel\0icon\x1f<span color='#fff'>󱎘</span>
Power off\0icon\x1f<span color='#fff'></span>
Reboot\0icon\x1f<span color='#fff'></span>
Sleep\0icon\x1f<span color='#fff'></span>
Hibernate\0icon\x1f<span color='#fff'></span>
Exit i3\0icon\x1f<span color='#fff'></span>"

len=`echo "$options" | wc -l`
choice=`echo -en "$options" | rofi -dmenu -p ">" -show-icons -i -l $len`

case $choice in
   "Power off")
      echo "Power off"
      systemctl poweroff
      ;;
   "Sleep")
      echo "Sleep"
      systemctl suspend
      ;;
   "Reboot")
      echo "Reboot"
      systemctl reboot
      ;;
   "Hibernate")
      echo "Hibernate"
      systemctl hibernate
      ;;
   "Exit i3")
      echo "Exit i3"
      i3-msg exit
      ;;
   *)
      echo "Canceled"
      ;;
esac