from sqlalchemy.orm import Session

from app.repositories.dm_repository import DMRepository


class DuplicateService:
    """
    Handles business rules related to duplicate DM prevention.
    """

    def __init__(self, db: Session):
        self.repository = DMRepository(db)

    def has_received_dm(
        self,
        *,
        recipient_user_id: str,
        rule_id: int,
    ) -> bool:
        """
        Check whether this user has already been associated
        with a DM for this rule.
        """

        existing_dm = self.repository.find_existing_for_user_and_rule(
            recipient_user_id=recipient_user_id,
            rule_id=rule_id,
        )

        return existing_dm is not None