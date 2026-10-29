# Recent keyboard layouts

The i3 startup launches `layout-switcher.sh`, which configures US, Russian, and
Ukrainian and runs a small X11/XKB event listener. It compiles the helper into
the user's cache on the first launch or after its source changes. Requirements:
a C compiler, libX11 headers, setxkbmap, and flock.

- Tap **Mod+Space**, then release Mod: switch to the previous layout.
- Hold **Mod** and tap **Space** again: visit the third layout. Release Mod to
  make that layout the most recently used. Holding Space does not auto-cycle.
- **Mod+Shift+Space** cycles in the opposite direction while Mod is held.
- **Mod+U** selects Ukrainian; **Mod+Shift+U** selects Russian. All three layouts
  remain available, and direct selections update the recent-layout order.

The initial fallback order is US, Russian, Ukrainian, with the active layout
moved to the front. Recent usage is kept for the life
of the helper. The per-display lock prevents duplicate listeners on i3 restarts.
The listener blocks waiting for X events and does not poll or grab ordinary typing.
Polybar's XKB module displays the selected layout immediately.

The old `grp:win_space_toggle` option must be removed because it switches layouts
in a fixed sequence independently of the helper. The launcher clears the XKB
options when configuring the three layouts.

Run `python3 sh/keyboard/test_layout_switcher.py` from the repository root to
exercise actual key events and XKB state in Xvfb. It requires Xvfb and libXtst
and automatically uses an isolated display.
