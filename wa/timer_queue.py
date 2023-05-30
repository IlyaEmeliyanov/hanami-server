
import asyncio
from queue import Queue

# Importing debugging module
import logging

class TimerQueue(Queue):
    def __init__(self, id: int, table_number: str, delay: int, size: int, ws):
        super().__init__(size)
        self.id = id
        self.table_number = table_number
        self.delay = delay
        self.counter = delay

        self.order = []
        self.background_tasks = None

        self.is_completed = False

        self.ws = ws


    def __str__(self):
        q_str = ""
        for q_item in self.queue:
            q_str += f"{q_item} <- "
        return f"[TIMER_QUEUE STATE]: Table {self.table_number}: ({q_str})"

    def get_cur_time(self):
        return self.counter

    def reset_timer(self):
        self.is_completed = False
        self.counter = self.delay

    def restart_timer(self):
        self.counter = self.delay
        self.background_tasks.add_task(self.start_timer)
        print(f"[LOG]: Timer {self.table_number} reset")

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
                    # If it is the first order inserted in the queue, then start the timer
                    self.background_tasks.add_task(self.start_timer)
                elif self.full(): # check if the newly inserted order fullfills the queue
                    print(f"[LOG]: Queue {self.table_number} is full")
                    print(self)

                    self.task_done()
                else:
                    print(f"[LOG]: Queue {self.table_number} is semi-full")
                    print(self)

                    # self.restart_timer()
            except Exception as exception:
                print(f"\n[ERROR] Something went wrong in timer_queue->enqueue_order: {exception}")
        else:
            print(f"[LOG] Queue {self.table_number} is already full")

    def dequeue_all(self):
        with self.mutex:
            self.queue.clear()
            print(f"[LOG]: Queue {self.table_number} cleared")

    def task_done(self):
        self.is_completed = True
        self.dequeue_all()
        self.reset_timer()

        try:
            self.ws.run(self.table_number, self.orders)
        except Exception as exception:
            print("[ERROR]: Something went wrong in timer_queue->task_done: ", exception)

    async def start_timer(self):
        print(f"[LOG]: Timer {self.table_number} started")
        self.is_completed = False
        while self.counter > 0 and not self.is_completed:
            self.counter -= 1
            await asyncio.sleep(1)
        print(f"[LOG]: Timer {self.table_number} finished")

        if not self.is_completed:
            self.task_done()