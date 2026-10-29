#!/bin/bash

if [[ $(~/linux/sh/is-night-mode.sh) == 1 ]]; then
   echo '%{T2}%{T-}'
else
   echo 
fi
