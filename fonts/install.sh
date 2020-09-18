#!/bin/bash

cp icon-fonts/fonts/icomoon.ttf ~/.fonts
cp fonts/* ~/.fonts

fc-cache -f -v

okMsg=OK
echo -e "\n\e[92m$okMsg\e[0m"
