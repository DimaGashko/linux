#!/bin/bash

cd ~/config/i3
exec 1>i3.config

wsGroup=$1

if [ ! -z $wsGroup ]; then
   sh/gen-ws-bindings.sh $wsGroup > i3.d/_workspaces.gen.i3
fi

for f in $(find i3.d/*)
do
   echo "# - - - - - - - - - - $f - - - - - - - - - -"
   cat $f
   echo -e "\n\n"
done