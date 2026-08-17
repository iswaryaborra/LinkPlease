from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.event import Event, WebhookEvent
from app.repositories.event_repository import EventRepository
from app.repositories.rule_repository import RuleRepository


class EventService:
    """
    Business logic for incoming webhook events.

    Responsibilities:
    - Detect duplicate event deliveries.
    - Persist new events.
    - Handle comment.created events.
    - Find rules matching the comment.
    """

    def __init__(self, db: Session):
        self.db = db
        self.event_repository = EventRepository(db)
        self.rule_repository = RuleRepository(db)

    def process_event(
        self,
        webhook_event: WebhookEvent,
    ) -> tuple[Event | None, bool]:
        """
        Process an incoming webhook event.

        Returns:
            (event, is_duplicate)

        If the event has already been received:
            (existing_event, True)

        If it is new:
            (new_event, False)
        """

        # First check whether we have already seen this event_id.
        existing_event = self.event_repository.get_by_event_id(
            webhook_event.event_id
        )

        if existing_event is not None:
            return existing_event, True

        data = webhook_event.data

        event = Event(
            event_id=webhook_event.event_id,
            event_type=webhook_event.event_type,
            comment_id=data.comment_id,
            post_id=data.post_id,
            user_id=(
                data.from_.user_id
                if data.from_ is not None
                else None
            ),
            username=(
                data.from_.username
                if data.from_ is not None
                else None
            ),
            comment_text=data.text,
            sent_at=webhook_event.sent_at,
        )

        try:
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)

        except IntegrityError:
            # Another request may have inserted the same event_id
            # between our initial check and this insert.
            self.db.rollback()

            existing_event = self.event_repository.get_by_event_id(
                webhook_event.event_id
            )

            if existing_event is not None:
                return existing_event, True

            raise

        return event, False

    def find_matching_rules(
        self,
        event: Event,
    ):
        """
        Find all rules matching the event's comment text.

        Deleted comments do not have comment text, so they cannot
        trigger a new DM.
        """

        if event.event_type != "comment.created":
            return []

        if not event.comment_text:
            return []

        return self.rule_repository.find_matching_rules(
            event.comment_text
        )