#!/bin/bash

options="Balanced\0icon\x1f<span color='#fff'></span>
Quiet\0icon\x1f<span color='#fff'></span>
Cool\0icon\x1f<span color='#fff'></span>
Performance\0icon\x1f<span color='#fff'></span>"

len=$(echo "$options" | wc -l)
choice=$(echo -en "$options" | rofi -dmenu -p ">" -show-icons -i -l $len)

if [[ -z $choice ]]; then
   echo "Cancelled"
   exit 0
fi

if [[ $choice == "Cool" ]]; then
   choice="cool-bottom"
fi

sudo smbios-thermal-ctl  --set-thermal-mode $choice

~/linux/sh/thermal/update-thermal.sh
