#!/bin/bash

exec rofi -dmenu -password -p "${SUDO_ASKPASS_PROMPT:-Password}"
