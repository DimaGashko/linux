# Helpers

- print unicode characters

```sh
echo -ne "\uf026"
```

- list fonts

```sh
fc-list
```

- print glyphs

```sh
xfd -fa /usr/share/fonts/TTF/fa5-solid-900.ttf
```

- update font cache
```sh
fc-cache -f -v
```

---
xfd -fa "Font Awesome 6 Free" -rows 40 -columns 50

xrdb -merge $HOME/.config/X11/.Xresources
----

Reset password lock after 3 failed attempts
faillock --reset

----
pacmd set-card-profile bluez_card.64_03_7F_DE_AC_3E  a2dp_sink

---
while read FONT; do echo "$FONT"; echo "$FONT"; xfd -fa "$FONT" -rows 40 -columns 50;  done < <(fc-list -f "%{family}\n" | grep Awesome)

---
sudo pacman -Sy archlinux-keyring && sudo pacman -Suy


----

```sh
xdg-mime query default image/png
```


Print power usage in watts, volts and amps and frequency
```sh
watch -n 1 "awk 'BEGIN {
  getline v < \"/sys/class/power_supply/ucsi-source-psy-USBC000:001/voltage_now\"
  getline a < \"/sys/class/power_supply/ucsi-source-psy-USBC000:001/current_now\"
  printf \"%.1f W (%.1f V × %.1f A)\\n\", v*a/1e12, v/1e6, a/1e6
}'"

watch -n 1 "grep 'cpu MHz' /proc/cpuinfo"

stress-ng --cpu 0 --timeout 600s
```

