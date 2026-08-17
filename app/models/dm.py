from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DM(Base):
    """
    Tracks a DM throughout its lifecycle.

    A DM can move through states such as:
        queued -> sending -> accepted -> delivered
                                  |
                                  -> failed
    """

    __tablename__ = "dms"

    __table_args__ = (
        UniqueConstraint(
            "rule_id",
    
            "recipient_user_id",
            name="uq_dm_rule_recipient",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    rule_id: Mapped[int] = mapped_column(
        ForeignKey("rules.id"),
        nullable=False,
        index=True,
    )

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id"),
        nullable=False,
        index=True,
    )

    recipient_user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    comment_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    pseudogram_dm_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="queued",
        index=True,
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    next_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )