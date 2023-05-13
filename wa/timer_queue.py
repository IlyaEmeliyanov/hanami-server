
import asyncio
from queue import Queue
from multiprocessing import Process
from threading import Timer

class TimerQueue(Queue):
    def __init__(self, id, delay, size, ws):
        super().__init__(size)
        self.id = id
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
        return f"[STATE]: Table {self.id}: ({q_str})"

    def reset_timer(self):
        self.is_completed = False
        self.counter = self.delay

    def restart_timer(self):
        self.counter = self.delay
        self.background_tasks.add_task(self.start_timer)
        print(f"[LOG]: RESET, Timer {self.id} reset")

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
                    print("[LOG]: FIRST, First element added")
                    print(self)
                    # If it is the first order inserted in the queue, then start the timer
                    self.background_tasks.add_task(self.start_timer)
                elif self.full(): # check if the newly inserted order fullfills the queue
                    print("[LOG]: FULL, Queue is full")
                    print(self)

                    self.task_done()
                else:
                    print("[LOG]: SEMI-FULL, queue contains some elements")
                    print(self)

                    # self.restart_timer()
            except Exception as exception:
                print(f"\n[❌] Something went wrong: {exception}")
        else:
            print("[💡] Queue is full")

    def complex_task(self, dishes):
        print("[LOG]: Dishes ", dishes)
        timer = Timer(10, self.callback)
        timer.start()

    def callback(self):
        print("[LOG]: Complex task finished")

    def dequeue_all(self):
        with self.mutex:
            self.queue.clear()
            print(f"[LOG]: CLEARED, Queue {self.id} cleared")

    def task_done(self):
        self.is_completed = True
        self.dequeue_all()
        self.reset_timer()

        print("ORDERS: ", self.orders)

        complex_process = Process(target=self.complex_task, args=(self.orders,))
        complex_process.start()

        # try:
        #     ws_process = Process(target=self.complex_task, args=(self.orders))
        #     ws_process.start()
        # except Exception as exception:
        #     print("[ERROR]: something went wrong in task_done ", exception)

        # try:
        #     self.ws.run(self.id, self.orders)
        #     # self.ws.run(self.table, self.orders)
        # except Exception as exception:
        #     print("[ERROR]: Something went wrong in task_done: ", exception)

    async def start_timer(self):
        print(f"[LOG]: STARTED, Timer {self.id} started")
        self.is_completed = False
        while self.counter > 0 and not self.is_completed:
            self.counter -= 1
            await asyncio.sleep(1)
        print(f"[LOG]: Timer finished: queue number {self.id}")

        if not self.is_completed:
            self.task_done()