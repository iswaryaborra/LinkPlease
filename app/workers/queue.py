import asyncio

from app.models.dm import DM


class DMQueue:
    """
    In-memory asynchronous queue for DM jobs.

    The actual DM job is already persisted in the database,
    so the queue only tells the worker that work is available.
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue[int] = asyncio.Queue()

    async def enqueue(self, dm: DM) -> None:
        """
        Add a DM database ID to the queue.
        """

        await self._queue.put(dm.id)

    async def dequeue(self) -> int:
        """
        Wait for the next DM ID.
        """

        return await self._queue.get()

    def task_done(self) -> None:
        """
        Mark the current queue item as completed.
        """

        self._queue.task_done()


# Shared queue used by the application.
dm_queue = DMQueue()