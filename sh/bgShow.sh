#!/bin/bash

speed=$1

while true
do
	feh ~/images/bg/* --bg-scale --randomize --no-fehbg
	sleep $speed
done