import asyncio
from datetime import datetime, timedelta, timezone

from app.clients.pseudogram_client import (
    PseudoGramClient,
    PseudoGramServerError,
    PseudoGramUnexpectedError,
)
from app.config.settings import get_settings
from app.database import SessionLocal
from app.repositories.dm_repository import DMRepository
from app.workers.queue import dm_queue


class DeliveryService:
    """
    Reconciles accepted DMs with their actual PseudoGram
    delivery status.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    async def reconcile_once(self) -> None:
        """
        Check accepted DMs and update their delivery status.
        """

        db = SessionLocal()

        try:
            repository = DMRepository(db)
            dms = repository.get_accepted()

            if not dms:
                return

            client = PseudoGramClient()

            try:
                for dm in dms:
                    if not dm.pseudogram_dm_id:
                        continue

                    try:
                        result = await client.get_dm_status(
                            dm.pseudogram_dm_id
                        )

                        if result.status == "delivered":
                            repository.update_delivery_status(
                                dm,
                                "delivered",
                            )

                        elif result.status == "failed":
                            await self.handle_delivery_failure(
                                dm,
                                repository,
                            )

                    except (
                        PseudoGramServerError,
                        PseudoGramUnexpectedError,
                    ):
                        # Temporary reconciliation failure.
                        # Leave the DM as accepted so the next
                        # reconciliation cycle can try again.
                        continue

            finally:
                await client.close()

        finally:
            db.close()

    async def handle_delivery_failure(
        self,
        dm,
        repository: DMRepository,
    ) -> None:
        """
        Handle a DM that PseudoGram reports as failed.
        """

        # If we've already reached the maximum number of
        # delivery attempts, permanently fail the DM.
        if dm.retry_count >= self.settings.delivery_max_attempts:
            repository.update_delivery_status(
                dm,
                "failed",
            )
            return

        next_retry_number = dm.retry_count + 1

        delay = self.settings.initial_retry_delay * (
            2 ** (next_retry_number - 1)
        )

        next_attempt_at = (
            datetime.now(timezone.utc)
            + timedelta(seconds=delay)
        )

        repository.increment_retry(
            dm,
            next_attempt_at=next_attempt_at,
        )

        # Wait for the calculated backoff before putting the
        # persistent DM job back into the sending queue.
        await asyncio.sleep(delay)

        await dm_queue.enqueue(dm)

    async def run_forever(self) -> None:
        """
        Continuously reconcile accepted DMs.
        """

        interval = (
            self.settings.delivery_check_interval_seconds
        )

        while True:
            try:
                await self.reconcile_once()

            except Exception as exc:
                print(
                    f"Delivery reconciliation error: {exc}"
                )

            await asyncio.sleep(interval)


delivery_service = DeliveryService()