"""Own exactly one bounded CPU-only stress-ng process group."""
import os
import shutil
import signal
import subprocess
import threading


class StressTest:
    def __init__(self):
        self.process = None
        self.stop_thread = None
        self.stopping = False

    def start(self, workers, load, seconds):
        if self.process is not None:
            raise RuntimeError('A test is already active')
        executable = shutil.which('stress-ng')
        if not executable:
            raise FileNotFoundError('Install stress-ng: sudo pacman -S stress-ng')
        if not 1 <= workers <= len(os.sched_getaffinity(0)) or not 1 <= load <= 100 or not 1 <= seconds <= 3600:
            raise ValueError('Invalid stress test settings')
        self.stopping = False
        self.process = subprocess.Popen(
            [executable, '--cpu', str(workers), '--cpu-load', str(load),
             '--timeout', f'{seconds}s', '--quiet'],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, start_new_session=True)

    @staticmethod
    def terminate(process):
        if process.poll() is not None:
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        except ProcessLookupError:
            process.wait()

    def stop(self):
        if self.process is not None and not self.stopping:
            self.stopping = True
            self.stop_thread = threading.Thread(target=self.terminate, args=(self.process,), name='stop-stress')
            self.stop_thread.start()

    def poll(self):
        if self.process is None:
            return None
        if self.stop_thread and self.stop_thread.is_alive():
            return None
        code = self.process.poll()
        if code is not None:
            self.process = None
            self.stop_thread = None
        return code

    def close(self):
        self.stop()
        if self.stop_thread:
            self.stop_thread.join()
        self.process = None
