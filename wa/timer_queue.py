
import asyncio
import time
from queue import Queue

# Importing modules
from wa.timer import Timer

class TimerQueue(Queue):
    # Init of the TimerQueue object
    def __init__(self, id: int, table_number: str, delay: int, waiting_delay: int, size: int, ws):
        super().__init__(size)
        self.id = id
        self.table_number = table_number
        self.delay = delay
        self.waiting_delay = waiting_delay
        self.counter = delay
        self.waiting_counter =  waiting_delay

        self.order = []

        self.timer = Timer(self.id, "Queue", self.table_number, self.delay, self.task_done)
        self.client_timer = Timer(self.id, "Client", self.table_number, self.waiting_delay, lambda: print(f"[LOG] Waiting timer {self.table_number} finished"))
        self.ws = ws

    # String representation of the current state of the queue
    def __str__(self):
        q_str = ""
        for q_item in self.queue:
            q_str += f"{q_item} <- "
        return f"[TIMER_QUEUE STATE]: Table {self.table_number}: ({q_str})"

    # Function that processes the enqueueing of the order
    def enqueue_order(self, order, background_tasks):
        first_time = self.empty() # checking if it's the first time you're enqueuing
        self.background_tasks = background_tasks
        if not self.full():
            try: # handling exception in case of ws failure
                for dish in order.dishes:
                    for _ in range(dish["quantity"]):
                        self.put(dish["dish"]) # insert order in the correct queue
                self.orders = list(self.queue)
                
                if first_time:
                    print(f"[LOG]: First element added to {self.table_number}")
                    print(self)

                    self.timer.start() # Start the timer on the first enqueued order

                elif self.full(): # check if the newly inserted order fullfills the queue
                    print(f"[LOG]: Queue {self.table_number} is full")
                    print(self)

                    self.timer.cancel() # Cancel the timer when the queue is full
                    self.task_done() # Send the order to the ws
                else:
                    print(f"[LOG]: Queue {self.table_number} is semi-full")
                    print(self)

                    self.timer.restart()
            except Exception as exception:
                print(f"\n[ERROR] Something went wrong in timer_queue->enqueue_order: {exception}")
        else:
            print(f"[LOG] Queue {self.table_number} is already full")

    # Clearing the queue
    def dequeue_all(self):
        with self.mutex:
            self.queue.clear()
            print(f"[LOG]: Queue {self.table_number} cleared")

    # Callback called when either one of the 2 conditions happen:
    # - Queue timer finishes
    # - The queue is full
    def task_done(self):
        self.dequeue_all() # Remove all the elements from current table queue
        self.client_timer.start() # Start the waiting timer

        try:
            self.ws.run(self.table_number, self.orders) # Run the webscraper
        except Exception as exception:
            print("[ERROR]: Something went wrong in timer_queue->task_done: ", exception)


