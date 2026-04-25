from collections.abc import Sequence

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_one
from app.core.database import get_db
from app.models import Run, TraceStep
from app.schemas import RunRead, TraceStepRead

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.get("/{item_id}", response_model=RunRead)
def read_run(item_id: str, db: Session = Depends(get_db)) -> Run:
    return get_one(db, Run, item_id)


@router.get("/{item_id}/trace", response_model=list[TraceStepRead])
def read_run_trace(item_id: str, db: Session = Depends(get_db)) -> Sequence[TraceStep]:
    return db.scalars(select(TraceStep).where(TraceStep.run_id == item_id).order_by(TraceStep.created_at)).all()
