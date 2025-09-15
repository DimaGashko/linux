#!/bin/bash

interval=0.25

i3-msg "workspace 1"
i3-msg "layout default"

# ssr 
alacritty --working-directory ~/ssr &

sleep $interval
i3-msg "split v"

alacritty --working-directory ~/ssr/frontend &

sleep $interval
i3-msg "split v"

# api
alacritty --working-directory ~/api &

sleep $interval
i3-msg "move right"
i3-msg "split v"

alacritty --working-directory ~/api -e bash -c "go run main.go config.json; bash" &

sleep $interval
i3-msg "split v"

# ab
# alacritty --working-directory ~/ab &

# sleep $interval
# i3-msg "move right"
# i3-msg "split v"

# alacritty --working-directory ~/ab -e bash -c "go run main.go config.json; bash" &

# code
code ~/ssr
code ~/api

