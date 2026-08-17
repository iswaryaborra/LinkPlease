from sqlalchemy.orm import Session

from app.models.rule import Rule, RuleCreateRequest
from app.repositories.rule_repository import RuleRepository


class RuleService:
    """Business logic for keyword rules."""

    def __init__(self, db: Session):
        self.repository = RuleRepository(db)

    def create_rule(self, request: RuleCreateRequest) -> Rule:
        """
        Create and persist a new keyword rule.
        """

        keyword = request.keyword.strip()
        dm_message = request.dm_message.strip()

        if not keyword:
            raise ValueError("Keyword cannot be empty.")

        if not dm_message:
            raise ValueError("DM message cannot be empty.")

        return self.repository.create(
            keyword=keyword,
            dm_message=dm_message,
        )