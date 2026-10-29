"""Run: python -m unittest discover -s tools/cpu-scope -v"""
from pathlib import Path
import tempfile
import unittest

from storage import Writer, connect, pack, query, repair_recent_outliers, unpack


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'history.sqlite3'
        self.db = connect(self.path)
        self.writer = Writer(self.db)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_rollups_preserve_weighted_mean_and_peaks_across_restart(self):
        self.writer.add(120, {0: (400, 10), -1: (400, 10)})
        self.writer.add(121, {0: (4400, 90), -1: (4400, 90)})
        self.writer.flush()
        resumed = Writer(self.db)
        resumed.add(122, {0: (1200, 20), -1: (1200, 20)})
        resumed.flush()
        row = self.db.execute('SELECT data FROM history WHERE resolution=60 AND ts=120').fetchone()
        v = unpack(row[0])[0]
        self.assertEqual(v, [3, 6000, 400, 4400, 120, 10, 90])

    def test_recent_view_uses_seconds_even_when_window_predates_install(self):
        for t in range(120, 130):
            self.writer.add(t, {0: (1000, 20)})
        self.writer.flush()
        points, level, _, _ = query(self.path, 0, 130, 0)
        self.assertEqual(level, 1)
        self.assertEqual(len(points), 10)

    def test_retention_keeps_old_history_and_falls_back_to_minutes(self):
        for t in (120, 180, 240, 300):
            self.writer.add(t, {0: (t * 10, 20)})
        self.writer.flush()
        self.writer.prune(250)
        points, level, _, extent = query(self.path, 120, 301, 0, average_seconds=3)
        self.assertEqual(level, 60)
        self.assertEqual(len(points), 4)
        self.assertEqual(extent, (120, 300))
        self.assertEqual(self.db.execute('SELECT count(*) FROM history WHERE resolution=1').fetchone()[0], 1)

    def test_year_query_uses_daily_index_and_bounded_points(self):
        blob = pack({0: [1, 1200, 400, 4000, 25, 0, 100]})
        self.db.executemany('INSERT INTO history VALUES (86400,?,?)', ((day * 86400, blob) for day in range(3650)))
        self.db.commit()
        points, level, _, _ = query(self.path, 0, 3650 * 86400, 0, max_points=900)
        self.assertEqual(level, 86400)
        self.assertLessEqual(len(points), 901)
        self.assertEqual(sum(p[1][0] for p in points), 3650)
        plan = self.db.execute('EXPLAIN QUERY PLAN SELECT ts,data FROM history WHERE resolution=? AND ts>=? AND ts<? ORDER BY ts', (86400, 0, 1000)).fetchone()[-1]
        self.assertIn('PRIMARY KEY', plan)

    def test_gaps_and_absent_cores_are_not_fabricated(self):
        self.writer.add(120, {0: (1000, 20)})
        self.writer.add(170, {1: (2000, 50)})
        self.writer.add(180, {0: (3000, 80)})
        self.writer.flush()
        points, _, _, _ = query(self.path, 120, 181, 0)
        self.assertEqual([p[0] for p in points], [120, 180])
        self.assertEqual(query(self.path, 120, 181, 99)[0], [])

    def test_all_cpus_keep_independent_values_and_missing_samples(self):
        self.writer.add(120, {-1: (1500, 30), 0: (1000, 20), 1: (2000, 40)})
        self.writer.add(121, {-1: (3000, 80), 1: (3000, 80)})
        self.writer.flush()
        points, _, _, _ = query(self.path, 120, 122, None)
        self.assertEqual(set(points[0][1]), {0, 1})
        self.assertEqual(set(points[1][1]), {1})
        for cpu in (0, 1):
            single = query(self.path, 120, 122, cpu)[0]
            self.assertEqual([(t, v[cpu]) for t, v in points if cpu in v], single)
        # The same bounded aggregate query handles long windows for every CPU.
        blob = pack({0: [2, 3000, 1000, 2000, 60, 20, 40],
                     1: [1, 4000, 4000, 4000, 90, 90, 90]})
        self.db.executemany('INSERT OR REPLACE INTO history VALUES (86400,?,?)',
                            ((day * 86400, blob) for day in range(3650)))
        self.db.commit()
        points, level, _, _ = query(self.path, 0, 3650 * 86400, None)
        self.assertEqual(level, 86400)
        self.assertLessEqual(len(points), 901)
        self.assertEqual(sum(v[0][0] for _, v in points), 7300)
        self.assertEqual(sum(v[1][0] for _, v in points), 3650)

    def test_selected_averaging_preserves_mean_peaks_and_fixed_buckets(self):
        for t, f, u in ((120, 1000, 10), (121, 3000, 50), (122, 2000, 30), (130, 4000, 90)):
            self.writer.add(t, {0: (f, u), 1: (f / 2, u / 2)})
        self.writer.flush()
        for seconds in (1, 2, 3, 10):
            points, _, step, _ = query(self.path, 120, 140, 0, average_seconds=seconds)
            self.assertEqual(step, seconds)
            self.assertEqual(sum(v[0] for _, v in points), 4)
        points, _, _, _ = query(self.path, 120, 140, None, average_seconds=10)
        self.assertEqual(points[0], (120, {0: [3, 6000, 1000, 3000, 90, 10, 50],
                                          1: [3, 3000, 500, 1500, 45, 5, 25]}))
        self.assertEqual(query(self.path, 121.5, 140, None, average_seconds=10)[0], points)
        self.writer.prune(130)
        _, level, step, _ = query(self.path, 60, 140, 0, average_seconds=3)
        self.assertEqual((level, step), (1, 3))

    def test_quarter_seconds_roll_up_and_expire_without_losing_history(self):
        for i in range(8):
            self.writer.add(120 + i / 4, {0: (1000 + i * 100, i * 10)})
        self.writer.flush()
        points, level, step, _ = query(self.path, 120, 121.75, 0, average_seconds=.25)
        self.assertEqual((len(points), level, step), (8, .25, .25))
        self.assertEqual([t for t, _ in points], [120+i/4 for i in range(8)])
        seconds = query(self.path, 120, 122, 0)[0]
        self.assertEqual(seconds[0][1], [4, 4600, 1000, 1300, 60, 0, 30])
        resumed = Writer(self.db)
        resumed.add(122, {0: (2000, 80)})
        resumed.flush()
        resumed.prune_high_resolution(121)
        self.assertEqual(self.db.execute('SELECT count(*) FROM history WHERE resolution=.25').fetchone()[0], 5)
        points, level, _, _ = query(self.path, 120, 122, 0, average_seconds=.25)
        self.assertEqual(level, 1)
        self.assertEqual(len(points), 3)
        self.assertEqual(sum(v[0] for _, v in points), 9)

    def test_open_reader_observes_atomic_flush(self):
        self.writer.add(120, {0: (1000, 20)})
        self.writer.flush()
        other = connect(self.path, readonly=True)
        self.writer.add(121, {0: (2000, 40)})
        self.writer.flush()
        self.assertEqual(other.execute('SELECT count(*) FROM history WHERE resolution=1').fetchone()[0], 2)
        other.close()

    def test_bad_quarter_second_sample_is_removed_from_every_resolution(self):
        self.writer.add(120, {-1: (750, 20), 0: (1000, 10), 1: (500, 30)})
        self.writer.add(120.25, {-1: (500500, 20), 0: (1000000, 10), 1: (1000, 30)})
        self.writer.add(120.5, {-1: (1250, 20), 0: (2000, 10), 1: (500, 30)})
        self.writer.flush()
        self.assertEqual(repair_recent_outliers(self.db, {0: 5000, 1: 5000, -1: 5000}), 1)
        raw = dict(self.db.execute('SELECT ts,data FROM history WHERE resolution=0.25'))
        repaired = unpack(raw[120.25])
        self.assertNotIn(0, repaired)
        self.assertEqual(repaired[-1][1], 1000)
        for resolution in (1, 60, 3600, 86400):
            blob = self.db.execute(
                'SELECT data FROM history WHERE resolution=? AND ts=?',
                (resolution, 120 // resolution * resolution)).fetchone()[0]
            values = unpack(blob)
            self.assertEqual(values[0], [2, 3000, 1000, 2000, 20, 10, 10])
            self.assertEqual(values[-1][0], 3)
            self.assertLessEqual(values[-1][3], 1250)
        self.assertEqual(repair_recent_outliers(self.db, {0: 5000, 1: 5000, -1: 5000}), 0)


if __name__ == '__main__':
    unittest.main()
