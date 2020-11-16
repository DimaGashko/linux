# Termite

A keyboard-centric VTE-based terminal, aimed at use within a window manager with tiling and/or tabbing support.

https://github.com/thestinger/termite

![](../../screenshots/2020-11-16_12-37.png)

# Helpers

```bash
# Reload config
killall -USR1 termite

# Reload config automatically
onchange ~/config/termite/termite.conf -- killall -USR1 termite
```
