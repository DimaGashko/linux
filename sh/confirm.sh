#!/bin/bash

options="YES\0icon\x1f<span color='#fff'></span>
NO\0icon\x1f<span color='#fff'></span>"

initialChoice=0

while [[ "$#" -gt 0 ]]; do
   case $1 in
   --preselect-no)
      initialChoice=1
      shift
      ;;
   esac
   shift
done

choice=$(echo -en "$options" | rofi -dmenu -p ">" -show-icons -i -l 2 -selected-row $initialChoice)

case $choice in
"YES")
   echo "YES"
   ;;
esac
