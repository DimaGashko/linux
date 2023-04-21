#!/bin/sh

# Returns the battery level of a bluetooth device with the given MAC address
# (or default device if not specified) as a percentage or an empty string if 
# the device is not connected.
#
# Note: make sure that `ExperimentalFeatures=true` is set in
# `/etc/bluetooth/main.conf` if bluetoothctl is showing the battery level.
#
# To verify run:
#
# $ bluetoothctl info
# 
# Device 64:03:7F:DE:AC:3E (public)
#  Name: Galaxy Buds Pro (AC3E)
#  ...
#  Battery Percentage: 0x17 (23)
#
# Usage:
# bluetooth-battery-level 64:03:7F:DE:AC:3E
# bluetooth-battery-level

bluetoothctl info $1 | awk -F '[()]' '/Battery Percentage/ {print $2}'