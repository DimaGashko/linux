focus_on_window_activation focus
floating_minimum_size 300 x 50
floating_maximum_size -1 x -1
default_floating_border pixel 1
hide_edge_borders both

for_window [window_role="pop-up"] floating enable
for_window [window_role="task_dialog"] floating enable
for_window [class="SimpleScreenRecorder"] floating enable
for_window [class="Gnome-control-center"] floating enable

for_window [class="feh"] floating enable
# for_window [class="feh"] resize set 1280 720
# for_window [class="feh"] move position center

for_window [class="AlacrittyFloating"] floating enable
for_window [class="Nm-connection-editor"] floating enable
for_window [class="flameshot"] floating enable
for_window [class="qt5ct"] floating enable