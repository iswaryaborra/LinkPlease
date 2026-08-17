from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dm import DM


class DMRepository:
    """Database operations related to outgoing DMs."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        rule_id: int,
        event_id: int,
        recipient_user_id: str,
        comment_id: str,
    ) -> DM:
        dm = DM(
            rule_id=rule_id,
            event_id=event_id,
            recipient_user_id=recipient_user_id,
            comment_id=comment_id,
            status="queued",
        )

        self.db.add(dm)
        self.db.commit()
        self.db.refresh(dm)

        return dm

    def get_by_id(self, dm_id: int) -> DM | None:
        statement = select(DM).where(DM.id == dm_id)

        return self.db.scalars(statement).first()

    def get_by_pseudogram_id(
        self,
        pseudogram_dm_id: str,
    ) -> DM | None:
        statement = select(DM).where(
            DM.pseudogram_dm_id == pseudogram_dm_id
        )

        return self.db.scalars(statement).first()

    def find_existing_for_user_and_rule(
        self,
        *,
        recipient_user_id: str,
        rule_id: int,
    ) -> DM | None:
        statement = select(DM).where(
            DM.recipient_user_id == recipient_user_id,
            DM.rule_id == rule_id,
        )

        return self.db.scalars(statement).first()

    def update_status(
        self,
        dm: DM,
        status: str,
    ) -> DM:
        dm.status = status

        self.db.commit()
        self.db.refresh(dm)

        return dm

    def mark_accepted(
        self,
        dm: DM,
        pseudogram_dm_id: str,
    ) -> DM:
        dm.pseudogram_dm_id = pseudogram_dm_id
        dm.status = "accepted"

        self.db.commit()
        self.db.refresh(dm)

        return dm

    def update_delivery_status(
        self,
        dm: DM,
        status: str,
    ) -> DM:
        """
        Update the delivery status of a DM.
        """

        dm.status = status

        self.db.commit()
        self.db.refresh(dm)

        return dm

    def increment_retry(
        self,
        dm: DM,
        next_attempt_at: datetime,
    ) -> DM:
        dm.retry_count += 1
        dm.next_attempt_at = next_attempt_at
        dm.status = "queued"

        self.db.commit()
        self.db.refresh(dm)

        return dm

    def get_queued(
        self,
        limit: int = 50,
    ) -> list[DM]:
        """
        Return a batch of queued DM jobs.
        """

        statement = (
            select(DM)
            .where(DM.status == "queued")
            .order_by(DM.id)
            .limit(limit)
        )

        return list(
            self.db.scalars(statement).all()
        )
    
    def get_accepted(
        self,
        limit: int = 50,
    ) -> list[DM]:
        """
        Return accepted DMs that need delivery reconciliation.
        """

        statement = (
            select(DM)
            .where(
                DM.status == "accepted",
                DM.pseudogram_dm_id.is_not(None),
            )
            .order_by(DM.id)
            .limit(limit)
        )

        return list(
            self.db.scalars(statement).all()
        )

    def find_by_comment_id(
        self,
        comment_id: str,
    ) -> DM | None:
        statement = select(DM).where(
            DM.comment_id == comment_id
        )

        return self.db.scalars(statement).first()