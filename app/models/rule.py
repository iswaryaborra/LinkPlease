from datetime import datetime, timezone

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Rule(Base):
    """
    Stores a keyword -> DM message rule.

    Example:
        keyword: PRICE
        dm_message: Here's the price list: ...
    """

    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    keyword: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    dm_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class RuleCreateRequest(BaseModel):
    """Request body for creating a keyword rule."""

    keyword: str = Field(
        min_length=1,
        max_length=255,
    )

    dm_message: str = Field(
        min_length=1,
    )


class RuleResponse(BaseModel):
    """Response returned after creating a rule."""

    rule_id: str
    keyword: str
    dm_message: str