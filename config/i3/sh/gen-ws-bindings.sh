#!/bin/bash

group=$1

for ws in {1..10}; do
   if [ $ws = "10" ]; then
      key="0"
   else
      key=$ws
   fi

   if [ $group -gt 0 ]; then
      ws=$(($group * 10 + $ws))
   fi

   echo "bindsym \$mod+$key workspace $ws"
   echo "bindsym \$mod+Shift+$key move container to workspace $ws"
   echo "bindsym \$mod+Ctrl+$key move container to workspace number $ws; workspace $ws"
done
