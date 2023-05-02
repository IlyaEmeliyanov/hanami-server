
from asyncio import sleep

from queue import Queue

from wa.order import Order

class TimerQueue(Queue):
    def __init__(self, id, delay, size):
        super().__init__(size)
        self.id = id
        self.delay = delay
        self.counter = delay
        self.is_canceled = False

        self.order = []
        self.background_tasks = None

    def get_state(self):
        return self.counter
    
    def set_state(self, state):
        self.counter = state

    def cancel_timer(self):
        self.is_canceled = True
        self.counter = 0
        print(f"[LOG]: CANCELLED, Timer {self.id} cancelled")

    def reset_timer(self):
        self.counter = self.delay
        self.is_canceled = False
        print(f"[LOG]: RESET, Timer {self.id} reset")

    def enqueue_order(self, order, background_tasks):
        first_time = self.empty() # checking if it's the first time you're enqueuing
        self.background_tasks = background_tasks
        if not self.full():
            try: # handling exception in case of ws failure
                self.put(Order(order.dishes)) # insert order in the correct queue
                print(self)

                self.orders = list(self.queue)
                
                if first_time:
                    print("[LOG]: FIRST, First element added")
                    # If it is the first order inserted in the queue, then start the timer
                    background_tasks.add_task(self.start_timer)
                elif self.full(): # check if the newly inserted order fullfills the queue
                    print("[LOG]: FULL, Queue is full")
                    self.task_done()
                else:
                    print("[LOG]: SEMI-FULL, queue contains some elements")
            except Exception as exception:
                print(f"\n[❌] Something went wrong: {exception}")
        else:
            print("[💡] Queue is full")

    async def complex_task(self, orders):
        for order in orders:
            print("[LOG]: Orders", order.dishes)

        import asyncio
        await asyncio.sleep(10)
        print("[LOG]: Complex task finished")

    def dequeue_all(self):
        with self.mutex:
            self.queue.clear()
            print(f"[LOG]: CLEARED, Queue {self.id} cleared")

    def task_done(self):
        self.reset_timer()
        self.dequeue_all()
        self.background_tasks.add_task(self.complex_task, self.orders)
        # ! background_tasks.add_task(ws.process, queue.id, orders)

    def __str__(self):
        q_str = ""
        for q_item in self.queue:
            q_str += f"{q_item} <- "
        return f"[STATE]: Table {self.id}: {q_str}"

    async def start_timer(self):
        print(f"[LOG]: STARTED, Timer {self.id} started")
        while self.counter > 0:
            self.counter -= 1
            await sleep(1)
        print(f"[LOG]: Timer finished: queue number {self.id}")

        self.task_done()