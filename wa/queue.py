
from time import sleep

from queue import Queue

class TimerQueue(Queue):
    def __init__(self, id, delay, size):
        super().__init__(size)
        self.id = id
        self.delay = delay
        self.counter = delay

    def get_state(self):
        return self.counter
    
    def set_state(self, state):
        self.counter = state

    def cancel_timer(self):
        self.counter = 0

    def __str__(self):
        q_str = ""
        for q_item in self.queue:
            q_str += f"{q_item} <- "
        return f"[ {q_str} ]"

    def start_timer(self):
        while self.counter > 0:
            self.counter -= 1
            sleep(1)
        print(f"[✅] Task complete: queue {self.id}")