import threading
import time

class Timer:
    def __init__(self, id: int, name: str, table_number: str, interval: int, callback):
        self.id = id
        self.table_number = table_number
        self.name = name
        self.interval = interval
        self.callback = callback
        self.timer = None
        self.is_canceled = False

    def _timer_callback(self):
        if not self.is_canceled:
            self.callback()
        self.timer = None

    def get_remaining_time(self):
        if self.timer is not None:
            return f"{(self.interval - time.time() + self.start_time):.0f}"
        return -1

    def start(self):
        print(f"[LOG]: {self.name} timer {self.table_number} {'re' if self.is_canceled else ''}started")
        self.is_canceled = False
        self.timer = threading.Timer(self.interval, self._timer_callback)
        self.timer.start()
        self.start_time = time.time()

    def restart(self):
        self.cancel()
        self.start()

    def cancel(self):
        print(f"[LOG]: {self.name} timer {self.table_number} canceled")
        if self.timer:
            self.is_canceled = True
            self.timer.cancel()
            self.timer = None
