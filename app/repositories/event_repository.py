from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import Event


class EventRepository:
    """Database operations related to webhook events."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_event_id(self, event_id: str) -> Event | None:
        statement = select(Event).where(Event.event_id == event_id)

        return self.db.scalars(statement).first()

    def create(
        self,
        *,
        event_id: str,
        event_type: str,
        comment_id: str,
        post_id: str | None,
        user_id: str | None,
        username: str | None,
        comment_text: str | None,
        sent_at,
    ) -> Event:

        event = Event(
            event_id=event_id,
            event_type=event_type,
            comment_id=comment_id,
            post_id=post_id,
            user_id=user_id,
            username=username,
            comment_text=comment_text,
            sent_at=sent_at,
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event

    def mark_processed(self, event: Event) -> Event:
        event.processed = True

        self.db.commit()
        self.db.refresh(event)

        return event