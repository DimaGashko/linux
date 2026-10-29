#!/bin/bash

set -eu

profile_file=/sys/firmware/acpi/platform_profile
choices_file=/sys/firmware/acpi/platform_profile_choices

options="Balanced\0icon\x1f<span font_desc='Custom System Icons 18' color='#fff'></span>
Quiet\0icon\x1f<span font_desc='Custom System Icons 18' color='#fff'></span>
Cool\0icon\x1f<span font_desc='Custom System Icons 18' color='#fff'></span>
Performance\0icon\x1f<span font_desc='Custom System Icons 18' color='#fff'></span>"

len=$(printf '%s\n' "$options" | wc -l)
choice=$(printf '%b' "$options" | rofi -dmenu -p ">" -show-icons -i -l "$len")

if [[ -z ${choice:-} ]]; then
    echo "Cancelled"
    exit 0
fi

profile=${choice,,}

if [[ ! -r $choices_file ]] || ! grep -qw -- "$profile" "$choices_file"; then
    printf 'Unsupported platform profile: %s\n' "$profile" >&2
    exit 1
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

if ! error=$(printf '%s\n' "$profile" | SUDO_ASKPASS="$script_dir/sudo-askpass.sh" sudo -A tee "$profile_file" 2>&1 >/dev/null); then
    rofi -e "Failed to set thermal profile to '$profile':

$error"
    exit 1
fi

if [[ $(<"$profile_file") != "$profile" ]]; then
    rofi -e "The thermal profile write completed, but the active profile did not change."
    exit 1
fi

~/linux/sh/thermal/update-thermal.sh
