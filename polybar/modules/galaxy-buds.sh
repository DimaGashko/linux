#!/bin/bash

if [[ $(bluetoothctl info) == *"Connected: yes"* ]]; then
   echo 
else 
   echo
fi