import asyncio
import time
from collections import deque


class RateLimiter:
    """
    Rolling-window rate limiter.

    Allows at most `max_requests` requests
    during `window_seconds`.
    """

    def __init__(
        self,
        max_requests: int = 10,
        window_seconds: float = 60.0,
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds

        self._timestamps: deque[float] = deque()

        # Protect the timestamp collection when multiple
        # async tasks use the limiter at the same time.
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """
        Wait until another request can safely be made.
        """

        while True:
            async with self._lock:
                now = time.monotonic()

                # Remove timestamps outside the rolling window.
                while (
                    self._timestamps
                    and now - self._timestamps[0]
                    >= self.window_seconds
                ):
                    self._timestamps.popleft()

                # We have capacity.
                if len(self._timestamps) < self.max_requests:
                    self._timestamps.append(now)
                    return

                # Calculate how long until the oldest
                # request leaves the rolling window.
                wait_time = (
                    self.window_seconds
                    - (now - self._timestamps[0])
                )

            await asyncio.sleep(wait_time)