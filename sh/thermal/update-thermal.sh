#!/bin/bash

profile=$(sudo smbios-thermal-ctl --get-thermal-info | grep "Current Thermal Modes" -A 1 | tail -n 1 | awk '{$1=$1};1')

echo $profile >/tmp/thermal-profile
echo $profile

# sudo smbios-thermal-ctl  --set-thermal-mode "Balanced"

# Supported Thermal Modes:
# 	 Balanced
# 	 Cool Bottom
# 	 Quiet
# 	 Performance
