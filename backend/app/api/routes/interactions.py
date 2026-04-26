from collections.abc import Sequence

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import UIInteractionEvent
from app.schemas import UIInteractionEventCreate, UIInteractionEventRead
from app.services.interactions.events import UIInteractionEventService

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


@router.post("", response_model=UIInteractionEventRead)
def create_interaction(payload: UIInteractionEventCreate, db: Session = Depends(get_db)) -> UIInteractionEvent:
    return UIInteractionEventService(db).create(
        workspace_id=payload.workspace_id,
        project_id=payload.project_id,
        user_id=payload.user_id,
        artifact_id=payload.artifact_id,
        block_id=payload.block_id,
        action_id=payload.action_id,
        run_id=payload.run_id,
        event_type=payload.event_type,
        payload_json=payload.payload,
    )


@router.get("", response_model=list[UIInteractionEventRead])
def list_interactions(
    workspace_id: str,
    artifact_id: str | None = None,
    run_id: str | None = None,
    event_type: str | None = None,
    db: Session = Depends(get_db),
) -> Sequence[UIInteractionEvent]:
    stmt = select(UIInteractionEvent).where(UIInteractionEvent.workspace_id == workspace_id)
    if artifact_id:
        stmt = stmt.where(UIInteractionEvent.artifact_id == artifact_id)
    if run_id:
        stmt = stmt.where(UIInteractionEvent.run_id == run_id)
    if event_type:
        stmt = stmt.where(UIInteractionEvent.event_type == event_type)
    return db.scalars(stmt.order_by(UIInteractionEvent.created_at.desc())).all()
