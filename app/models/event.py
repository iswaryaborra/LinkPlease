from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from pydantic import BaseModel, Field

class Event(Base):
    """
    Stores incoming PseudoGram webhook events.

    event_id is unique because PseudoGram can redeliver
    the same event multiple times.
    """

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    event_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    comment_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    post_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    user_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    comment_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    processed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    duplicates_blocked: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
)

class WebhookUser(BaseModel):
    """User who created the comment."""

    user_id: str
    username: str


class WebhookData(BaseModel):
    """Data contained inside a webhook event."""

    comment_id: str
    post_id: str | None = None
    text: str | None = None
    created_at: datetime | None = None
    from_: WebhookUser | None = Field(
        default=None,
        alias="from",
   )

    model_config = {
        "populate_by_name": True,
    }


class WebhookEvent(BaseModel):
    """Incoming PseudoGram webhook event."""

    event_id: str
    event_type: str
    sent_at: datetime
    data: WebhookData
