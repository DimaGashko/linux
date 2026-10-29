# CPU Scope

A small native dark GTK4 app for CPU clock speed, utilization, and persistent history.
Designed for this Arch Linux / i3 machine. No web runtime, pip packages, root daemon,
or network access. Frequency is read from `/proc/cpuinfo`, like `grep 'cpu MHz'`.
**MHz is frequency, not CPU load**: utilization is measured separately from deltas
in `/proc/stat`. Logical CPUs include SMT threads; this i7-12700H has 20 logical
CPUs across 14 physical cores.

## Start

```sh
~/.local/bin/cpu-scope
```

Or search **CPU Scope** in your application launcher (rofi's `drun` mode).
The recorder starts automatically with your systemd user session and continues
when the window closes. It records only while the computer/user service is running;
suspend, shutdown, and time before installation cannot be reconstructed.
The window runs as a systemd user service so it remains independent of the terminal
or launcher that opened it. If it crashes, systemd restarts it after three seconds;
closing the window normally stops it. Launching CPU Scope again while it is already
open focuses its existing window, including when i3 has it behind another tab.

- Left list: mint numbers show live MHz for every logical CPU; amber bars show
  utilization. Hover a row for the exact percentage. A high clock speed can
  coincide with low utilization: speed and time spent busy are different measurements.
- CPU labels run from **CPU 01** through **CPU 20** on this machine. These are
  display names: CPU 01 is Linux logical CPU 0, CPU 02 is CPU 1, and so on.
- Select **All CPUs** for the mean across online logical CPUs, or a CPU for its history.
- In **All CPUs**, use the adjacent **Average / Separate CPUs** radio buttons above the chart to overlay every
  logical CPU in its own color, on both charts. The legend identifies CPUs; click a
  legend entry to inspect that CPU alone. Hover a line to see the nearest CPU’s values.
  Separate mode shows mean lines without overlapping min/max shading.
- Top numbers always show **current** readings, even while browsing history.
- The temperature is the highest available CPU sensor; not per-core temperature.
- **Refresh**: set live chart updates to every 0.25–30 seconds (default 1 second).
  This is independent of averaging; sampling and recording run four times per second.
- **Chart average**: drag the slider from 0.25 to 60 seconds (default 1 second).
  This averages both charts into fixed time buckets, keeping min/max bands.
  Live sidebar readings and stored history stay unchanged. Wide windows or old
  summaries can require coarser averaging; the effective interval is shown beside
  the slider. The newest bucket may still be incomplete.
- Choose 1 minute through 30 days, or **All history**.
- Drag the plot, scroll, use the arrows, or scrub the bottom timeline to move in time.
- **Ctrl + scroll** changes the visible duration.
- Enter a local date such as `2026-10-21 09:30` and press Enter to set the window's
  right edge. For a whole previous day, select 24 hours and enter the following midnight.
- **Resume live** returns to the newest samples.
- Hover the chart to inspect a timestamp, MHz, and utilization.
- Thin lines show averages; shaded bands preserve minimum and maximum peaks.
  Missing intervals remain gaps (outages shorter than a summary bucket can be averaged within it).

## CPU stress test

Expand **Stress test** below the chart to choose workers, requested load per worker,
and duration (1–3,600 seconds). **Start test / Stop test** stays visible when the
settings are collapsed. Defaults: one worker per available logical CPU, 100% requested load, 5 minutes (300 seconds).
Starting returns the chart to live view. Worker count is independent of the selected
chart CPU; the scheduler decides which CPUs run the workers.

Uses the installed `stress-ng` executable with `--cpu`, `--cpu-load`, and `--timeout`.
If missing, install with `sudo pacman -S stress-ng`. The app runs only CPU workers,
stops automatically at the duration limit, and stops its test when the window closes.
Stop targets only the process group started by CPU Scope, leaving other tests alone.
The UI shows remaining time and completion/error status. No test runs automatically
when the app opens or the section expands.

## Storage and resource usage

Database: `${XDG_DATA_HOME:-~/.local/share}/cpu-scope/history.sqlite3`.
Latest readings are published atomically in `$XDG_RUNTIME_DIR/cpu-scope/latest.json`
(normally RAM-backed `/run/user/1000`).

Default retention:

| Resolution | Retention |
| --- | --- |
| 0.25 seconds | Latest hour (pruned once per minute) |
| 1 second | 7 days |
| 1 minute, 1 hour, 1 day | Forever |

This keeps the complete recorded time span available, with reduced detail for old data.
Summaries retain sample counts, means, minima and maxima **for every logical CPU**.
No cloud service is involved. The database grows with retained history; summary
storage growth is much slower than raw samples. Actual size depends on CPU count
and variation. Freed raw-history pages are reused; the file does not automatically shrink.

To keep **every one-second sample forever**, run:

```sh
systemctl --user edit cpu-scope-recorder.service
```

Add this override, substituting your actual home path if different:

```ini
[Service]
ExecStart=
ExecStart=/usr/bin/python /home/dg/.local/share/cpu-scope/app/recorder.py --raw-days 0
```

Then `systemctl --user restart cpu-scope-recorder`. Any positive `--raw-days N`
sets a different retention. Removed raw samples cannot be recovered from summaries.

The recorder samples and commits every 0.25 seconds, and
uses SQLite WAL. Closing normally flushes pending data; an abrupt power loss can still lose recent writes because SQLite uses NORMAL
synchronization. Charts refresh from storage every second by default (configurable
from 0.25–30 seconds); sidebar and top readings always refresh once per second, independently of the chart setting.
One-second rows now summarize four samples. Subsecond detail begins with this update;
older readings cannot be reconstructed. Use a short range and 0.25-second chart
averaging to see individual samples. Longer views automatically aggregate points
to keep drawing bounded. Views crossing the high-resolution retention boundary
fall back to one-second history. Summary buckets are UTC-aligned; display timestamps use local time.

Frequency readings are checked against each CPU's reported hardware maximum,
with 10% tolerance for reporting jitter. Impossible values are omitted from
new samples and chart queries. If an older subsecond sample contaminated a
summary, stop the recorder and run `python repair_history.py` from this folder.
The repair utility makes a timestamped SQLite backup before rebuilding only
the affected time buckets; then restart the recorder. It needs the affected
quarter-second samples to still be within the latest hour.

An index on `(resolution, ts)` restricts reads to the visible window. The app selects
an appropriate stored resolution before reading, returns about 900 points, and retains
only that result. A single worker handles queries off the GTK thread; obsolete query
results are discarded. Database cache is capped at 2 MiB per connection. Long-range
queries stream coarse summaries without retaining off-screen samples. No per-frame
animation, polling subprocesses, or hidden history widgets. The UI defaults to
Cairo software rendering with GL/Vulkan initialization disabled to avoid needless
driver allocations. Set `GSK_RENDERER=gl` explicitly if you prefer GPU rendering.

## Install / update / remove

All dependencies were already present on this machine:

```sh
sudo pacman -S python python-gobject python-cairo gtk4 libadwaita
./install.sh
```

The dependency command is only needed on a new machine. The installer copies source
into the user data directory, installs `~/.local/bin/cpu-scope`, a desktop entry,
and recorder/window user services. Re-run it after editing source; close/reopen the UI to load changes.
No changes to i3 configuration are needed.

```sh
systemctl --user status cpu-scope-recorder
journalctl --user -u cpu-scope-recorder
systemctl --user status cpu-scope-ui
journalctl --user -u cpu-scope-ui
systemctl --user stop cpu-scope-recorder       # pause recording
systemctl --user start cpu-scope-recorder      # resume recording
./uninstall.sh                               # preserves your history
```

To back up live history consistently, use SQLite's backup API rather than copying
only the main file while WAL writes are active:

```sh
python - <<'PY'
import os, sqlite3
from pathlib import Path
p = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'cpu-scope/history.sqlite3'
with sqlite3.connect(p) as source, sqlite3.connect('cpu-scope-backup.sqlite3') as dest:
    source.backup(dest)
PY
```

## Development / verification

```sh
python app.py
python -m unittest discover -s . -v
GTK_A11Y=none dbus-run-session -- xvfb-run -a python app.py --smoke-test
```

`storage.py` owns indexed persistence, retention and queries; `recorder.py` owns
sampling; `app.py` owns the GTK interface and bounded Cairo rendering.
The smoke test opens the actual window and exercises range selection, panning,
date jumps, CPU selection and returning live, then closes it.

## UI choice and design references

Inspection found GTK3/4, libadwaita, Qt5/6, PyGObject and PyCairo installed; no
PySide/PyQt bindings. GTK4 works under i3/X11 without running GNOME and avoids
installing another toolkit binding or using a browser runtime.

The visual references were [Resources](https://apps.gnome.org/Resources/) and
[Mission Center](https://missioncenter.io/), including their published screenshots:
compact processor navigation, subdued chart grids, native dark controls, and clear
units. CPU Scope uses graphite surfaces, mint frequency lines and amber utilization,
without dashboard card grids, gradients or decorative animation.
