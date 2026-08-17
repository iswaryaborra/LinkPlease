from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.rule import RuleCreateRequest, RuleResponse
from app.services.rule_service import RuleService


router = APIRouter(
    prefix="/rules",
    tags=["Rules"],
)


@router.post(
    "",
    response_model=RuleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_rule(
    request: RuleCreateRequest,
    db: Session = Depends(get_db),
) -> RuleResponse:
    """
    Create a keyword -> DM rule.
    """

    try:
        service = RuleService(db)
        rule = service.create_rule(request)

        return RuleResponse(
            rule_id=str(rule.id),
            keyword=rule.keyword,
            dm_message=rule.dm_message,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc