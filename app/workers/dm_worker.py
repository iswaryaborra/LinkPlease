import asyncio
from datetime import datetime, timezone

from app.clients.pseudogram_client import (
    PseudoGramBadRequestError,
    PseudoGramClient,
    PseudoGramRateLimitError,
    PseudoGramServerError,
)
from app.config.settings import get_settings
from app.database import SessionLocal
from app.repositories.dm_repository import DMRepository
from app.repositories.rule_repository import RuleRepository
from app.utils.retry import RetryPolicy
from app.workers.queue import dm_queue
from app.utils.rate_limiter import RateLimiter


MAX_RECONCILIATION_ATTEMPTS = 5
RECONCILIATION_DELAY_SECONDS = 2


class DMWorker:
    """
    Background worker responsible for sending queued DMs.

    Handles:
    - DM sending
    - duplicate-safe retries
    - 400 permanent failures
    - 429 rate limiting
    - 500 temporary failures
    - delivery reconciliation
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.retry_policy = RetryPolicy()
        self.rate_limiter = RateLimiter(
            max_requests=self.settings.rate_limit_requests,
            window_seconds=self.settings.rate_limit_window_seconds,
       )

    async def process_dm(self, dm_id: int) -> None:
        """
        Process one persisted DM job.
        """

        db = SessionLocal()

        try:
            dm_repository = DMRepository(db)
            rule_repository = RuleRepository(db)

            dm = dm_repository.get_by_id(dm_id)

            if dm is None:
                return

            if dm.status in {
                "delivered",
                 "failed",
                 "cancelled",
                 }:
                return

            rule = rule_repository.get_by_id(dm.rule_id)

            if rule is None:
                dm_repository.update_status(dm, "failed")
                return

            dm_repository.update_status(
                dm,
                "sending",
            )

            client = PseudoGramClient()

            try:
                result = await self._send_with_retry(
                    dm=dm,
                    rule=rule,
                    client=client,
                )

                if result is None:
                    return

                dm_repository.mark_accepted(
                    dm,
                    pseudogram_dm_id=result.dm_id,
                )

                # Reconcile delivery in the background.
                asyncio.create_task(
                    self.reconcile_dm(
                        dm_id=dm.id,
                        pseudogram_dm_id=result.dm_id,
                    )
                )

            finally:
                await client.close()

        finally:
            db.close()

    async def _send_with_retry(
        self,
        *,
        dm,
        rule,
        client,
    ):
        """
        Send a DM with retry handling.

        400:
            Permanent failure.

        429:
            Retry using Retry-After.

        500:
            Retry using exponential backoff.
        """

        max_attempts = self.retry_policy.max_attempts

        for attempt in range(1, max_attempts + 1):

            try:
                await self.rate_limiter.acquire()
                return await client.send_dm(
                    recipient_user_id=dm.recipient_user_id,
                    message=rule.dm_message,
                    comment_id=dm.comment_id,
                    idempotency_key=f"dm-{dm.id}",
                )

            except PseudoGramBadRequestError:
                # Permanent failure. Never retry.
                db = SessionLocal()

                try:
                    repository = DMRepository(db)

                    current_dm = repository.get_by_id(dm.id)

                    if current_dm:
                        repository.update_status(
                            current_dm,
                            "failed",
                        )

                finally:
                    db.close()

                return None

            except PseudoGramRateLimitError as exc:

                if attempt >= max_attempts:
                    db = SessionLocal()

                    try:
                        repository = DMRepository(db)

                        current_dm = repository.get_by_id(dm.id)

                        if current_dm:
                            repository.update_status(
                                current_dm,
                                "failed",
                            )

                    finally:
                        db.close()

                    return None

                # For 429, respect Retry-After.
                retry_delay = exc.retry_after

                print(
                    f"DM {dm.id}: rate limited. "
                    f"Retrying in {retry_delay} seconds."
                )

                await asyncio.sleep(retry_delay)

                continue

            except PseudoGramServerError:

                if attempt >= max_attempts:
                    db = SessionLocal()

                    try:
                        repository = DMRepository(db)

                        current_dm = repository.get_by_id(dm.id)

                        if current_dm:
                            repository.update_status(
                                current_dm,
                                "failed",
                            )

                    finally:
                        db.close()

                    return None

                retry_delay = self.retry_policy.get_delay(
                    attempt
                )

                print(
                    f"DM {dm.id}: PseudoGram server error. "
                    f"Retrying in {retry_delay} seconds."
                )

                await asyncio.sleep(retry_delay)

        return None

    async def reconcile_dm(
        self,
        *,
        dm_id: int,
        pseudogram_dm_id: str,
    ) -> None:
        """
        Check the delivery status of an accepted DM.
        """

        for attempt in range(
            1,
            MAX_RECONCILIATION_ATTEMPTS + 1,
        ):

            try:
                client = PseudoGramClient()

                try:
                    result = await client.get_dm_status(
                        pseudogram_dm_id
                    )

                finally:
                    await client.close()

                db = SessionLocal()

                try:
                    repository = DMRepository(db)

                    dm = repository.get_by_id(dm_id)

                    if dm is None:
                        return

                    if result.status == "delivered":
                        repository.update_delivery_status(
                            dm,
                            "delivered",
                        )

                        print(
                            f"DM {dm_id} delivered successfully."
                        )

                        return

                    if result.status == "failed":
                        if (
                            dm.retry_count
                            >= self.settings.delivery_max_attempts
                        ):
                            repository.update_delivery_status(
                                dm,
                                "failed",
                            )

                            print(
                                f"DM {dm_id} delivery failed "
                                f"permanently after "
                                f"{dm.retry_count} retries."
                            )

                            return

                        repository.increment_retry(
                            dm,
                            next_attempt_at=datetime.now(
                                timezone.utc
                            ),
                        )

                        print(
                            f"DM {dm_id} delivery failed. "
                            f"Retrying attempt "
                            f"{dm.retry_count}."
                        )

                        await dm_queue.enqueue(dm.id)

                        return

                    if result.status == "queued":
                        print(
                            f"DM {dm_id} still queued. "
                            f"Reconciliation attempt "
                            f"{attempt}/"
                            f"{MAX_RECONCILIATION_ATTEMPTS}."
                        )

                finally:
                    db.close()

            except PseudoGramServerError:
                print(
                    f"Temporary error while checking "
                    f"DM {dm_id} delivery status."
                )

            except Exception as exc:
                print(
                    f"Unexpected reconciliation error "
                    f"for dm_id={dm_id}: {exc}"
                )

            if attempt < MAX_RECONCILIATION_ATTEMPTS:
                await asyncio.sleep(
                    RECONCILIATION_DELAY_SECONDS
                )

        print(
            f"DM {dm_id} could not be reconciled after "
            f"{MAX_RECONCILIATION_ATTEMPTS} attempts."
        )

    async def run_forever(self) -> None:
        """
        Continuously process DM jobs from the queue.
        """

        while True:
            dm_id = await dm_queue.dequeue()

            try:
                await self.process_dm(dm_id)

            except Exception as exc:
                print(
                    f"Unexpected DM worker error for "
                    f"dm_id={dm_id}: {exc}"
                )

            finally:
                dm_queue.task_done()


dm_worker = DMWorker()