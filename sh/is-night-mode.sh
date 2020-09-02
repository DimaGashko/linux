#!/bin/bash

if [ ! -f /tmp/night ]; then
   echo 0
   exit
fi

cat /tmp/night