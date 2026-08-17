from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.dm import DM
from app.models.event import Event


router = APIRouter(
    prefix="/stats",
    tags=["Stats"],
)


@router.get("")
def get_stats(
    db: Session = Depends(get_db),
) -> dict:
    """
    Return live DM statistics in the format
    required by the assignment.
    """

    sent = db.scalar(
        select(func.count(DM.id)).where(
            DM.status == "delivered"
        )
    ) or 0

    failed = db.scalar(
        select(func.count(DM.id)).where(
            DM.status == "failed"
        )
    ) or 0

    queued = db.scalar(
        select(func.count(DM.id)).where(
            DM.status == "queued"
        )
    ) or 0

    duplicates_blocked = db.scalar(
        select(
            func.coalesce(
                func.sum(Event.duplicates_blocked),
                0,
            )
        )
    ) or 0

    return {
        "sent": sent,
        "failed": failed,
        "queued": queued,
        "duplicates_blocked": duplicates_blocked,
    }