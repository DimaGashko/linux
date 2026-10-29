#!/bin/bash

set -eu

profile_file=/sys/firmware/acpi/platform_profile

if [[ ! -r $profile_file ]]; then
    echo "Platform profile is unavailable" >&2
    exit 1
fi

profile=$(<"$profile_file")
printf '%s\n' "${profile^}"
