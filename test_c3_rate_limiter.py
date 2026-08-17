import asyncio
import time

from app.utils.rate_limiter import RateLimiter


async def main():
    limiter = RateLimiter(
        max_requests=10,
        window_seconds=5,
    )

    start = time.monotonic()

    for i in range(11):
        await limiter.acquire()

        elapsed = time.monotonic() - start

        print(
            f"Request {i + 1}: "
            f"{elapsed:.2f} seconds"
        )


if __name__ == "__main__":
    asyncio.run(main())
    