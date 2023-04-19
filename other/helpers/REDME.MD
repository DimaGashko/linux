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


xfd -fa "Font Awesome 6 Free" -rows 40 -columns 50