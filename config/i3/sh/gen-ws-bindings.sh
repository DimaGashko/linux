#!/bin/bash

for i in {1..10}; do
   echo "bindsym \$mod+$i workspace $i"
   echo "bindsym \$mod+Shift+$i move container to workspace $i"
   echo "bindsym \$mod+Ctrl+$i move container to workspace number $i; workspace $i"
done
