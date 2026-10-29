"""Bounded, multi-resolution SQLite history. No GUI dependencies."""
from pathlib import Path
import os
import math
import sqlite3
import struct
import zlib

LEVELS = (0.25, 1, 60, 3600, 86400)
RECORD = struct.Struct('<iI6d')


def frequency_limits():
    """Maximum plausible MHz per logical CPU, with room for reporting jitter."""
    root = Path('/sys/devices/system/cpu')
    limits = {}
    for path in root.glob('cpu[0-9]*/cpufreq/cpuinfo_max_freq'):
        try:
            limits[int(path.parent.parent.name[3:])] = int(path.read_text()) / 1000 * 1.1
        except (OSError, ValueError):
            pass
    limits[-1] = max(limits.values(), default=10000)
    return limits


def valid_frequency(cpu, value, limits):
    return (value[0] > 0 and math.isfinite(value[2]) and math.isfinite(value[3])
            and 0 < value[2] <= value[3] <= limits.get(cpu, 10000))


def data_dir():
    return Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'cpu-scope'


def runtime_dir():
    return Path(os.environ.get('XDG_RUNTIME_DIR', data_dir())) / 'cpu-scope'


def pack(values):
    return zlib.compress(b''.join(RECORD.pack(cpu, *v) for cpu, v in sorted(values.items())), 1)


def unpack(blob):
    return {r[0]: list(r[1:]) for r in RECORD.iter_unpack(zlib.decompress(blob))}


def merge(target, source):
    for cpu, v in source.items():
        if cpu not in target:
            target[cpu] = v.copy()
        else:
            a = target[cpu]
            a[0] += v[0]
            a[1] += v[1]
            a[2] = min(a[2], v[2])
            a[3] = max(a[3], v[3])
            a[4] += v[4]
            a[5] = min(a[5], v[5])
            a[6] = max(a[6], v[6])


def connect(path=None, readonly=False):
    path = Path(path or data_dir() / 'history.sqlite3')
    if readonly:
        db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=2)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(path, timeout=5)
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA synchronous=NORMAL')
        db.execute('CREATE TABLE IF NOT EXISTS history (resolution INTEGER, ts INTEGER, data BLOB NOT NULL, PRIMARY KEY(resolution, ts)) WITHOUT ROWID')
    db.execute('PRAGMA cache_size=-2048')
    return db


class Writer:
    def __init__(self, db):
        self.db = db
        self.current = {}
        self.pending = []
        for level in LEVELS[1:]:
            row = db.execute('SELECT ts,data FROM history WHERE resolution=? ORDER BY ts DESC LIMIT 1', (level,)).fetchone()
            if row:
                self.current[level] = (row[0], unpack(row[1]))

    def add(self, ts, readings):
        values = {int(cpu): [1, f, f, f, u, u, u] for cpu, (f, u) in readings.items()}
        if not values:
            return
        self.pending.append((0.25, math.floor(ts * 4) / 4, pack(values)))
        for level in LEVELS[1:]:
            bucket = int(ts) // level * level
            old, aggregate = self.current.get(level, (bucket, {}))
            if old != bucket:
                self.pending.append((level, old, pack(aggregate)))
                aggregate = {}
            merge(aggregate, values)
            self.current[level] = (bucket, aggregate)

    def flush(self):
        rows = self.pending + [(r, t, pack(v)) for r, (t, v) in self.current.items()]
        with self.db:
            self.db.executemany('INSERT OR REPLACE INTO history VALUES (?,?,?)', rows)
        self.pending.clear()

    def prune_high_resolution(self, before):
        with self.db:
            self.db.execute('DELETE FROM history WHERE resolution=0.25 AND ts IN (SELECT ts FROM history WHERE resolution=0.25 AND ts<? LIMIT 10000)', (before,))

    def prune(self, before):
        # Bounded deletion; freed SQLite pages are reused, no expensive VACUUM.
        with self.db:
            self.db.execute('DELETE FROM history WHERE resolution=1 AND ts IN (SELECT ts FROM history WHERE resolution=1 AND ts<? LIMIT 10000)', (before,))


def bounds(db):
    first = db.execute('SELECT ts FROM history WHERE resolution=60 ORDER BY ts LIMIT 1').fetchone()
    last = db.execute('SELECT ts FROM history WHERE resolution=0.25 ORDER BY ts DESC LIMIT 1').fetchone()
    if last is None:
        last = db.execute('SELECT ts FROM history WHERE resolution=1 ORDER BY ts DESC LIMIT 1').fetchone()
    return (first[0], last[0]) if first and last else None


def query(path, start, end, cpu=-1, max_points=900, average_seconds=1):
    """Read only intersecting indexed buckets, return <= max_points+1 points.

    Averaging uses fixed UTC-aligned buckets, weighted counts and preserved extrema.
    cpu=None returns every logical CPU in each bucket, with one indexed scan.
    Old raw data falls back to minute summaries. Coarser levels are selected
    BEFORE fetching, so a year view doesn't scan a year of second samples.
    """
    if average_seconds < 0.25 or not math.isfinite(average_seconds):
        raise ValueError('Averaging interval must be finite and at least 0.25 seconds')
    db = connect(path, readonly=True)
    try:
        limits = frequency_limits()
        extent = bounds(db)
        span = max(0.25, end - start)
        # Read quarter-second rows only when the visible detail benefits from them.
        target = max(average_seconds, span / max_points)
        if span <= 3600:
            level = 0.25 if target < 1 else 1
        else:
            level = next((r for r in LEVELS[1:] if span / r <= max_points), LEVELS[-1])
        if level == 0.25:
            first = db.execute('SELECT ts FROM history WHERE resolution=0.25 ORDER BY ts LIMIT 1').fetchone()
            first_second = db.execute('SELECT ts FROM history WHERE resolution=1 ORDER BY ts LIMIT 1').fetchone()
            if not first or (first_second and start < first[0] and first_second[0] < math.floor(first[0])):
                level = 1
        if level == 1:
            first = db.execute('SELECT ts FROM history WHERE resolution=1 ORDER BY ts LIMIT 1').fetchone()
            if first and extent and start < first[0] and extent[0] < first[0] // 60 * 60:
                level = 60
        step = math.ceil(max(level, span / max_points, average_seconds) / level) * level
        result, current, current_t = [], {}, None
        cursor = db.execute('SELECT ts,data FROM history WHERE resolution=? AND ts>=? AND ts<? ORDER BY ts',
                            (level, math.floor(start / step) * step, end + 0.000001))
        for t, blob in cursor:
            key = t // step
            if key != current_t and current:
                result.append((current_t * step, (current if cpu is None else current[cpu])))
                current = {}
            current_t = key
            values = {c: v for c, v in unpack(blob).items() if valid_frequency(c, v, limits)}
            if cpu is None:
                merge(current, {c: v for c, v in values.items() if c >= 0})
            elif cpu in values:
                merge(current, {cpu: values[cpu]})
        if current:
            result.append((current_t * step, (current if cpu is None else current[cpu])))
        return result, level, step, extent
    finally:
        db.close()


def repair_recent_outliers(db, limits=None):
    """Rebuild buckets touched by invalid quarter-second readings.

    Run with the recorder stopped. All levels are rebuilt in order, leaving
    unaffected buckets and the original SQLite file untouched.
    """
    limits = limits or frequency_limits()
    affected = set()
    repaired_samples = 0
    rows = db.execute('SELECT ts,data FROM history WHERE resolution=0.25').fetchall()
    with db:
        for ts, blob in rows:
            values = unpack(blob)
            bad = [cpu for cpu, value in values.items()
                   if cpu >= 0 and not valid_frequency(cpu, value, limits)]
            if not bad:
                continue
            for cpu in bad:
                del values[cpu]
            repaired_samples += 1
            # The aggregate is a per-sample mean of the remaining valid CPUs.
            cpus = [v for cpu, v in values.items() if cpu >= 0]
            if cpus:
                values[-1] = [1, *(sum(v[i] for v in cpus) / len(cpus) for i in (1, 2, 3, 4, 5, 6))]
            else:
                values.pop(-1, None)
            db.execute('UPDATE history SET data=? WHERE resolution=0.25 AND ts=?', (pack(values), ts))
            affected.add(math.floor(ts))
        for level, source in ((1, 0.25), (60, 1), (3600, 60), (86400, 3600)):
            next_affected = set()
            for bucket in affected:
                target = math.floor(bucket / level) * level
                if target in next_affected:
                    continue
                combined = {}
                for (blob,) in db.execute(
                    'SELECT data FROM history WHERE resolution=? AND ts>=? AND ts<?',
                    (source, target, target + level)):
                    merge(combined, unpack(blob))
                if combined:
                    db.execute('INSERT OR REPLACE INTO history VALUES (?,?,?)',
                               (level, target, pack(combined)))
                next_affected.add(target)
            affected = next_affected
    return repaired_samples
