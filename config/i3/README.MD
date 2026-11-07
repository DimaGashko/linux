# i3 workspaces

**Mod+Ctrl+S** runs the selected XScreenSaver animation on all displays.
The shortcut uses the saver number from `xscreensaver-command --time`.
On idle, XScreenSaver blanks the displays and powers them off after 15 minutes.
Locking is disabled in `~/.xscreensaver`.

Hold **Mod** and type a workspace number. Every digit switches immediately and
restarts a **300 ms** timer for extending the number. Expiry or releasing the last
Mod key ends the sequence without switching again. There is no fixed digit count
and no workspace group to select first.

- `Mod+1`, then `2` within 300 ms: immediately visit `1`, then `12`.
- Add `3` within another 300 ms: immediately visit `123`.
- Wait more than 300 ms between `1` and `2`: visit `1`, then `2`.
- Hold **Shift** as well to move the initially focused container through each
  intermediate workspace and follow it. This also works with a parent container.
- An initial **0 key** opens workspace `10`; **grave (`)** still opens `0`.
  Both contribute a zero digit when extending a number, so `01` still selects
  the common workspace. Leading zeros are removed (`001` → `1`),
  except `01`, `02`, and `03`, which select the common workspaces.
- **Minus**, **equals/plus**, and **Backspace** open `A`, `B`, and `C` immediately.
  Shift moves and follows; the previous Ctrl variants still move and follow.
  Home keeps its workspace `124` shortcut.
- Any other i3 binding runs normally and ends the number sequence. Nothing
  enters an i3 binding mode or grabs the keyboard. Unbound keys remain unaffected.
- Holding a digit does not append auto-repeat digits. Tap it again to enter `11`.
- Changing between switch and move while typing starts a new sequence.
  Keep Shift held throughout a move sequence.

The common workspaces are named `A`, `B`, and `C`. Polybar uses i3's order
(`index-sort = false`) to keep them after numeric workspaces. The existing
`01`, `02`, and `03` input sequences remain aliases for `A`, `B`, and `C`.
Slack opens on `C`; System Monitor opens on `B`. Other numeric workspaces keep
their names, including `10`, entered as `1`, `0`. Ctrl+digit is no longer reserved
for workspace groups.

`gen-i3.sh` combines the checked-in `i3.d/*.i3` fragments, checks the candidate
with `i3 -C`, then replaces the generated `i3.config` atomically. The `config`
symlink points there. Mod+Shift+C regenerates and reloads; Mod+Shift+R regenerates
and restarts i3.

`sh/workspace-input.py` listens to i3's binding events and XKB modifier changes.
It needs Python 3 and libX11, with no additional Python packages. It captures the
focused container at the start of a move sequence so a focus change between
digits cannot move a different window. A per-display lock prevents duplicate
listeners, and the helper reconnects after i3 restarts. It sleeps when idle.
The common-workspace bindings use native i3 commands and do not need the helper.

Change `--timeout-ms 300` in `i3.d/startup.i3` to tune the interval between digits.
Switching remains immediate regardless of this setting. After changing it, stop
the helper, then use Mod+Shift+R to start it with the new value:

```sh
pkill -u "$USER" -f '^python3 .*/i3/sh/workspace-input.py( |$)'
```

Run the integration tests from the repository root:

```sh
python3 config/i3/sh/test_workspace_input.py
```

They start a separate i3 session under Xvfb and generate actual key events.
Requirements: i3, Polybar, Xvfb/xvfb-run, libXtst, libX11, and setxkbmap.

The pre-change Git backup is `backup/workspaces-before-number-input-2026-10-29`.
The ignored active config and group state were also copied to
`~/.cache/i3-workspace-backup-2026-10-29/` before removal.
