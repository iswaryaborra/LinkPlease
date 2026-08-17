from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.dm import DM
from app.models.event import Event
from app.models.rule import Rule
from app.repositories.dm_repository import DMRepository


class DMService:
    """
    Business logic for creating DM jobs.

    This service does NOT directly call PseudoGram.

    It creates a persistent DM job with status='queued'.
    A background worker will later send it.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = DMRepository(db)

    def create_dm_job(
        self,
        *,
        event: Event,
        rule: Rule,
    ) -> tuple[DM | None, bool]:
        """
        Create a queued DM for a matching rule.

        Returns:
            (dm, created)

        created=True:
            A new DM job was created.

        created=False:
            A DM for this user/rule already exists.
        """

        if not event.user_id:
            return None, False

        # First check normally.
        existing_dm = self.repository.find_existing_for_user_and_rule(
            recipient_user_id=event.user_id,
            rule_id=rule.id,
        )

        if existing_dm is not None:
            return existing_dm, False

        try:
            dm = self.repository.create(
                rule_id=rule.id,
                event_id=event.id,
                recipient_user_id=event.user_id,
                comment_id=event.comment_id,
            )

            return dm, True

        except IntegrityError:
            # Protect against two webhook requests attempting to
            # create the same user/rule DM at the same time.
            self.db.rollback()

            existing_dm = (
                self.repository.find_existing_for_user_and_rule(
                    recipient_user_id=event.user_id,
                    rule_id=rule.id,
                )
            )

            if existing_dm is not None:
                return existing_dm, False

            raise