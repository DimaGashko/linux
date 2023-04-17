#!/bin/bash

speed=$1

while true
do
	feh ~/linux/other/bg-images/* --bg-scale --randomize --no-fehbg
	sleep $speed
done