import asyncio
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv


load_dotenv()

API_URL = "http://127.0.0.1:8000/webhook"
SECRET = os.getenv("PSEUDOGRAM_API_KEY")

TOTAL_EVENTS = 500
CONCURRENCY = 20


def create_event(index: int) -> tuple[bytes, str]:
    payload = {
        "event_id": f"evt_c3_load_{index:04d}",
        "event_type": "comment.created",
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "data": {
            "comment_id": f"cmt_c3_load_{index:04d}",
            "post_id": f"post_c3_load_{index:04d}",
            "text": "PRICE please",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "from": {
                "user_id": f"usr_c3_load_{index:04d}",
                "username": f"c3_load_user_{index:04d}",
            },
        },
    }

    body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    signature = hmac.new(
        SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    return body, f"sha256={signature}"


async def send_event(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    index: int,
):
    body, signature = create_event(index)

    async with semaphore:
        try:
            response = await client.post(
                API_URL,
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-PseudoGram-Signature": signature,
                },
            )

            return index, response.status_code

        except Exception as exc:
            return index, f"ERROR: {exc}"


async def main():
    if not SECRET:
        raise RuntimeError(
            "PSEUDOGRAM_API_KEY is missing from .env"
        )

    semaphore = asyncio.Semaphore(CONCURRENCY)

    start = time.monotonic()

    async with httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(
            max_connections=CONCURRENCY,
            max_keepalive_connections=CONCURRENCY,
        ),
    ) as client:

        tasks = [
            send_event(
                client,
                semaphore,
                index,
            )
            for index in range(1, TOTAL_EVENTS + 1)
        ]

        results = await asyncio.gather(*tasks)

    elapsed = time.monotonic() - start

    successful = sum(
        1
        for _, status in results
        if status == 200
    )

    failed = [
        (index, status)
        for index, status in results
        if status != 200
    ]

    print()
    print("=" * 50)
    print("C3 LOAD TEST RESULT")
    print("=" * 50)
    print(f"Total events:       {TOTAL_EVENTS}")
    print(f"Successful:         {successful}")
    print(f"Failed:             {len(failed)}")
    print(f"Time taken:         {elapsed:.2f} seconds")
    print(f"Within 10 seconds:  {elapsed <= 10}")
    print()

    if failed:
        print("Failed requests:")
        for item in failed[:20]:
            print(item)

        if len(failed) > 20:
            print(
                f"... and {len(failed) - 20} more"
            )

    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())