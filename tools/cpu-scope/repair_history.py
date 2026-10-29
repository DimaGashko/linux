"""Remove impossible quarter-second readings and rebuild affected summaries.

Stop cpu-scope-recorder.service before running. A SQLite backup is saved first.
"""
import argparse
from datetime import datetime
import fcntl
import os
from pathlib import Path
import sqlite3

from storage import data_dir, repair_recent_outliers, runtime_dir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=data_dir() / 'history.sqlite3')
    args = parser.parse_args()
    os.umask(0o077)
    runtime_dir().mkdir(parents=True, exist_ok=True)
    with (runtime_dir() / 'recorder.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error('stop cpu-scope-recorder.service before repairing history')
        if not args.database.is_file():
            parser.error(f'database not found: {args.database}')
        backup = args.database.with_name(
            f'{args.database.stem}-before-repair-{datetime.now():%Y%m%d-%H%M%S}.sqlite3')
        with sqlite3.connect(args.database) as db, sqlite3.connect(backup) as saved:
            db.backup(saved)
            repaired = repair_recent_outliers(db)
        print(f'Repaired {repaired} invalid sample(s). Backup: {backup}')


if __name__ == '__main__':
    main()
