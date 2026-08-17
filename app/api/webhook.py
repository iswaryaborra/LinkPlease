from fastapi import APIRouter, Header, HTTPException, Request, status
from starlette.concurrency import run_in_threadpool

from app.config.settings import get_settings
from app.database import SessionLocal
from app.models.event import WebhookEvent
from app.repositories.dm_repository import DMRepository
from app.services.dm_service import DMService
from app.services.event_service import EventService
from app.utils.signature import verify_webhook_signature
from app.workers.queue import dm_queue


router = APIRouter(
    prefix="/webhook",
    tags=["Webhook"],
)


def process_webhook_database(
    webhook_event: WebhookEvent,
):
    """
    Perform all blocking database work in a worker thread.

    Returns:
        response data,
        DM IDs that need to be queued.
    """

    db = SessionLocal()

    try:
        event_service = EventService(db)

        # -----------------------------------------------------
        # Part A: Process event and detect duplicates.
        # -----------------------------------------------------
        event, is_duplicate = event_service.process_event(
            webhook_event
        )

        # Repeated event_id must not create another DM.
        if is_duplicate:
            return (
                {
                    "status": "ok",
                    "duplicate": True,
                    "event_id": webhook_event.event_id,
                },
                [],
            )

        # -----------------------------------------------------
        # C2: Handle comment.deleted events.
        # -----------------------------------------------------
        if event.event_type == "comment.deleted":
            dm_repository = DMRepository(db)

            dm = dm_repository.find_by_comment_id(
                event.comment_id
            )

            if dm is not None and dm.status in {
                "queued",
                "sending",
            }:
                dm_repository.update_status(
                    dm,
                    "cancelled",
                )

            return (
                {
                    "status": "ok",
                    "duplicate": False,
                    "event_id": webhook_event.event_id,
                    "deleted": True,
                },
                [],
            )

        # -----------------------------------------------------
        # Normal comment.created processing.
        # -----------------------------------------------------
        matching_rules = event_service.find_matching_rules(
            event
        )

        dm_service = DMService(db)

        queued_count = 0
        duplicate_dm_count = 0

        # Store IDs instead of SQLAlchemy objects.
        # This prevents DetachedInstanceError after db.commit().
        dms_to_queue = []

        for rule in matching_rules:
            dm, created = dm_service.create_dm_job(
                event=event,
                rule=rule,
            )

            if dm is None:
                continue

            if created:
                queued_count += 1

                # Store the ID while the object is still attached
                # to the active SQLAlchemy session.
                dms_to_queue.append(dm.id)

            else:
                duplicate_dm_count += 1

        event.duplicates_blocked = duplicate_dm_count

        # Commit all database changes.
        db.commit()

        response = {
            "status": "ok",
            "duplicate": False,
            "event_id": webhook_event.event_id,
            "matching_rules": len(matching_rules),
            "queued_dms": queued_count,
            "duplicate_dms": duplicate_dm_count,
        }

        return response, dms_to_queue

    finally:
        db.close()


@router.post(
    "",
    status_code=status.HTTP_200_OK,
)
async def receive_webhook(
    request: Request,
    webhook_event: WebhookEvent,
    signature: str | None = Header(
        default=None,
        alias="X-PseudoGram-Signature",
    ),
) -> dict:
    """
    Receive and process an incoming PseudoGram webhook event.

    Flow:
    1. Verify HMAC signature.
    2. Perform blocking database work in a threadpool.
    3. Queue newly-created DM jobs using their IDs.
    """

    settings = get_settings()

    # ---------------------------------------------------------
    # Part B: Verify webhook signature FIRST.
    # ---------------------------------------------------------
    raw_body = await request.body()

    is_valid = verify_webhook_signature(
        raw_body=raw_body,
        signature_header=signature or "",
        secret=settings.pseudogram_api_key,
    )

    if not is_valid:
        print(
            "WARNING: Invalid webhook signature received. "
            "Rejecting request."
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    # ---------------------------------------------------------
    # Move synchronous SQLAlchemy work off the async event loop.
    # ---------------------------------------------------------
    response, dm_ids_to_queue = await run_in_threadpool(
        process_webhook_database,
        webhook_event,
    )

    # ---------------------------------------------------------
    # Queue only after the database transaction has completed.
    # ---------------------------------------------------------
    for dm_id in dm_ids_to_queue:
        await dm_queue.enqueue(dm_id)

    return response
