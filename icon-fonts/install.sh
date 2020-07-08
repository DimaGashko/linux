#!/bin/bash

cp fonts/icomoon.ttf ~/.fonts
fc-cache -f -v

okMsg=OK
echo -e "\n\e[92m$okMsg\e[0m"