"""One small background recorder, independent of the window."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import time

from storage import Writer, connect, frequency_limits, runtime_dir


class Sampler:
    def __init__(self):
        self.previous = {}
        self.frequency_limits = frequency_limits()
        self.temperatures = []
        for hw in Path('/sys/class/hwmon').glob('hwmon*'):
            try:
                if (hw / 'name').read_text().strip() in ('coretemp', 'k10temp', 'zenpower'):
                    self.temperatures.extend(hw.glob('temp*_input'))
            except OSError:
                pass

    def sample(self):
        frequencies, cpu = {}, None
        for line in Path('/proc/cpuinfo').read_text().splitlines():
            key, _, value = line.partition(':')
            if key.strip() == 'processor':
                cpu = int(value)
            elif key.strip() == 'cpu MHz' and cpu is not None:
                try:
                    mhz = float(value)
                except ValueError:
                    continue
                if 0 < mhz <= self.frequency_limits.get(cpu, 10000):
                    frequencies[cpu] = mhz
        readings = {}
        for line in Path('/proc/stat').read_text().splitlines():
            fields = line.split()
            if not fields or not fields[0].startswith('cpu') or not fields[0][3:].isdigit():
                continue
            cpu = int(fields[0][3:])
            ticks = [int(x) for x in fields[1:9]]  # guest ticks already included in user/nice
            total, idle = sum(ticks), ticks[3] + ticks[4]
            prev = self.previous.get(cpu)
            self.previous[cpu] = (total, idle)
            if cpu not in frequencies or prev is None:
                continue
            dt, di = total - prev[0], idle - prev[1]
            usage = max(0, min(100, 100 * (dt - di) / dt)) if dt > 0 else 0
            readings[cpu] = (frequencies[cpu], usage)
        if readings:
            readings[-1] = tuple(sum(v[i] for v in readings.values()) / len(readings) for i in (0, 1))
        temps = []
        for path in self.temperatures:
            try:
                temps.append(float(path.read_text()) / 1000)
            except (OSError, ValueError):
                pass
        return readings, max(temps) if temps else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw-days', type=int, default=7, help='Second-resolution retention; 0 keeps forever. Summaries always retained.')
    args = parser.parse_args()
    if args.raw_days < 0:
        parser.error('--raw-days must be nonnegative')
    os.umask(0o077)
    runtime_dir().mkdir(parents=True, exist_ok=True)
    lock = (runtime_dir() / 'recorder.lock').open('w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('CPU Scope recorder is already running')
    db = connect()
    writer, sampler = Writer(db), Sampler()
    writer.prune_high_resolution(time.time() - 3600)
    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    count = 0
    try:
        while running:
            deadline = time.monotonic() + .25
            now = time.time()
            readings, temperature = sampler.sample()
            if readings:
                writer.add(now, readings)
                writer.flush()
                payload = {'ts': now, 'cpus': readings, 'temperature': temperature, 'raw_days': args.raw_days, 'sample_seconds': .25}
                tmp = runtime_dir() / 'latest.tmp'
                tmp.write_text(json.dumps(payload))
                tmp.replace(runtime_dir() / 'latest.json')
                count += 1
                if count % 240 == 0:
                    writer.prune_high_resolution(now - 3600)
                    if args.raw_days:
                        writer.prune(now - args.raw_days * 86400)
            time.sleep(max(0, deadline - time.monotonic()))
    finally:
        writer.flush()
        db.close()


if __name__ == '__main__':
    main()
