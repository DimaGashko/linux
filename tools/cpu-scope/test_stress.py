import shutil
import time
import unittest
from stress_test import StressTest


@unittest.skipUnless(shutil.which('stress-ng'), 'stress-ng is optional')
class StressTests(unittest.TestCase):
    def setUp(self):
        self.test = StressTest()

    def tearDown(self):
        self.test.close()

    def test_timeout_and_restart(self):
        self.test.start(1, 10, 1)
        process = self.test.process
        self.assertEqual(process.wait(timeout=10), 0)
        self.assertEqual(self.test.poll(), 0)
        self.test.start(1, 10, 30)
        self.test.stop()
        self.test.close()
        self.assertIsNone(self.test.process)

    def test_stop_does_not_stop_other_test(self):
        other = StressTest()
        try:
            other.start(1, 10, 15)
            self.test.start(1, 10, 15)
            time.sleep(.2)
            owned = self.test.process
            self.test.close()
            self.assertIsNotNone(owned.poll())
            self.assertIsNone(other.process.poll())
        finally:
            other.close()

    def test_no_duplicate_or_invalid_start(self):
        with self.assertRaises(ValueError):
            self.test.start(0, 100, 30)
        self.test.start(1, 10, 15)
        with self.assertRaises(RuntimeError):
            self.test.start(1, 10, 15)
