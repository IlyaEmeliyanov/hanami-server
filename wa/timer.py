
import asyncio


class Timer:
    def __init__(self, timeout, callback):
        self.timeout = timeout
        self.callback = callback
        self.task = asyncio.ensure_future(self.job())

    async def job(self):
        await asyncio.sleep(self.timeout)
        await self.callback()

    def cancel(self):
        self.task.cancel()
