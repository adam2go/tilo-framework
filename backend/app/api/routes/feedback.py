from collections.abc import Sequence

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Feedback
from app.schemas import FeedbackCreate, FeedbackRead
from app.services.improvement.candidates import SkillCandidateService
from app.services.improvement.metrics import RunMetricsService

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.get("", response_model=list[FeedbackRead])
def list_feedback(workspace_id: str, run_id: str | None = None, db: Session = Depends(get_db)) -> Sequence[Feedback]:
    stmt = select(Feedback).where(Feedback.workspace_id == workspace_id)
    if run_id:
        stmt = stmt.where(Feedback.run_id == run_id)
    return db.scalars(stmt.order_by(Feedback.created_at.desc())).all()


@router.post("", response_model=FeedbackRead)
def create_feedback(payload: FeedbackCreate, db: Session = Depends(get_db)) -> Feedback:
    item = Feedback(**payload.model_dump())
    db.add(item)
    db.flush()
    if item.run_id:
        RunMetricsService(db).apply_feedback_score(item.run_id, item.rating)
    SkillCandidateService(db).maybe_create_from_feedback(item)
    db.commit()
    db.refresh(item)
    return item
