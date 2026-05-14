from collections.abc import Sequence

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from tilo.api.deps import get_one
from tilo.core.database import get_db
from tilo.models import Run, RunMetrics, SurfaceTurn, TraceStep
from tilo.schemas import RunMetricsRead, RunRead, SurfaceTurnRead, TraceStepRead

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.get("/{item_id}", response_model=RunRead)
def read_run(item_id: str, db: Session = Depends(get_db)) -> Run:
    return get_one(db, Run, item_id)


@router.get("/{item_id}/trace", response_model=list[TraceStepRead])
def read_run_trace(item_id: str, db: Session = Depends(get_db)) -> Sequence[TraceStep]:
    return db.scalars(select(TraceStep).where(TraceStep.run_id == item_id).order_by(TraceStep.created_at)).all()


@router.get("/{item_id}/metrics", response_model=RunMetricsRead)
def read_run_metrics(item_id: str, db: Session = Depends(get_db)) -> RunMetrics:
    return db.scalar(select(RunMetrics).where(RunMetrics.run_id == item_id)) or get_one(db, RunMetrics, item_id)


@router.get("/{item_id}/surface-turns", response_model=list[SurfaceTurnRead])
def read_run_surface_turns(item_id: str, db: Session = Depends(get_db)) -> Sequence[SurfaceTurn]:
    """List the SurfaceTurns produced by a Run, in emission order.

    This is the canonical "what did the agent render this run?" endpoint.
    Renderers can pull this after a /messages call to display the surfaces;
    a future SSE companion will emit each turn as it is persisted.
    """
    return db.scalars(
        select(SurfaceTurn)
        .where(SurfaceTurn.run_id == item_id)
        .order_by(SurfaceTurn.ordinal.asc(), SurfaceTurn.created_at.asc())
    ).all()
