#!/bin/bash

function title {
   echo "# - - - - - - - - - - $1 - - - - - - - - - -"
}

for f in $(find i3.d/*)
do
   title $f
   cat $f
   echo -e "\n\n"
done

title "workspaces"
sh/gen-ws-bindings.sh