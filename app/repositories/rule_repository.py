from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rule import Rule


class RuleRepository:
    """Database operations related to rules."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, keyword: str, dm_message: str) -> Rule:
        rule = Rule(
            keyword=keyword,
            dm_message=dm_message,
        )

        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)

        return rule

    def get_all(self) -> list[Rule]:
        statement = select(Rule).order_by(Rule.id)

        return list(self.db.scalars(statement).all())

    def find_matching_rules(self, comment_text: str) -> list[Rule]:
        """
        Find all rules whose keyword occurs anywhere in the
        comment, using case-insensitive matching.
        """

        comment_lower = comment_text.lower()

        rules = self.get_all()

        return [
            rule
            for rule in rules
            if rule.keyword.lower() in comment_lower
        ]

    def get_by_id(self, rule_id: int) -> Rule | None:
        statement = select(Rule).where(Rule.id == rule_id)

        return self.db.scalars(statement).first()