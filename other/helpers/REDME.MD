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