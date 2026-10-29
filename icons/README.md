# Custom System Icons

Rounded outline icons for system applications, with the real
OpenAI logo and the familiar `@` workspace symbol. Sources use a 24×24 grid;
original drawings use rounded caps/joins and a 1.7-unit stroke (2.2 for the clock
and thermometers, for readability in the 24px bar). See [NOTICE.md](NOTICE.md) for the
OpenAI and `@` SVG attribution.

The CPU glyph uses a rounded chip outline. The thermal-profile and shutdown Rofi
menus also use this font, including the power, restart, logout, cancel, and
hibernate symbols. Their icon markup selects `Custom System Icons` explicitly.

## Build and install

Requires Python 3 with venv/pip, Inkscape, and fontconfig. The first build downloads
the pinned Python dependencies into `icons/.venv` (no system Python changes).

```sh
./icons/build.sh    # SVG sources -> validated TTF + SVG contact sheet
./icons/install.sh  # rebuild, install for the current user, refresh fontconfig
i3-msg 'exec --no-startup-id ~/config/polybar/bin/launch.sh'
```

The installed font is `Custom System Icons`, under
`~/.local/share/fonts/custom-system-icons/` (or `$XDG_DATA_HOME/fonts/…`).
`dist/CustomSystemIcons.ttf` is also included for installation without rebuilding.
The installer does not restart the bar automatically.

## Edit or add icons

Edit the individual SVG files in `src/`. Keep their 24×24 viewBox. Then rebuild
and reinstall. `manifest.json` defines the stable private-use Unicode mappings;
add new mappings without renumbering existing ones. Inkscape expands the source
strokes into filled outlines before fontTools compiles the TrueType font.
The build checks that every glyph is present, nonempty, and inside the font bounds.

Polybar uses font slot 2 (`font-1`) at 13.5pt / 18px on the bar's 96-DPI canvas.
Every icon advances 18px. The clock, thermometer, and thermal-profile drawings
are scaled to 5/6 size inside their SVG canvases. The explicit font DPI avoids this system's fontconfig
75-DPI default turning a pixel size into an unexpected point size.
The `fast-badge` glyph has a dot already drawn at the bottom-right of the same
canvas: overlay it after the OpenAI logo with `%{O-18}` and set the red color.
No per-character vertical tags or separate dot font are needed.

`dist/preview.svg` is the source contact sheet. `dist/polybar-preview.png` shows
the compiled font rendered by Polybar, including default/fast assistant states.
Regenerate it with `./icons/preview.py` after installation; it requires Polybar,
Xvfb (`xvfb-run`), and `timeout` and uses an isolated display, leaving your bar alone.

The application-controlled system tray (e.g. nm-applet and Slack) supplies its own
images; those are not font glyphs and are not replaced by this set.

## Restarting Polybar

The i3 shortcut is Mod+O. The launcher finds bars in the current X11 session,
stops them, and starts bars only for connected, configured monitors. It uses
`setsid` and `nohup` with redirected stdin/stdout/stderr so its children survive
the launching shell. Logs are in `~/.cache/polybar/` (or `$XDG_CACHE_HOME/polybar/`).
When restarting from an automation or agent, dispatch through `i3-msg` as above
so the bar inherits i3's desktop environment.
