from collections.abc import Sequence

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from tilo.api.deps import get_one
from tilo.core.database import get_db
from tilo.models import Confirmation
from tilo.schemas import ConfirmationApproveRequest, ConfirmationEditRequest, ConfirmationRead, ConfirmationRejectRequest

router = APIRouter(prefix="/api/confirmations", tags=["confirmations"])


@router.get("", response_model=list[ConfirmationRead])
def list_confirmations(workspace_id: str, status: str | None = Query(default="pending"), db: Session = Depends(get_db)) -> Sequence[Confirmation]:
    stmt = select(Confirmation).where(Confirmation.workspace_id == workspace_id)
    if status:
        stmt = stmt.where(Confirmation.status == status)
    return db.scalars(stmt.order_by(Confirmation.created_at.desc())).all()


@router.get("/{item_id}", response_model=ConfirmationRead)
def read_confirmation(item_id: str, db: Session = Depends(get_db)) -> Confirmation:
    return get_one(db, Confirmation, item_id)


@router.post("/{item_id}/approve", response_model=ConfirmationRead)
def approve_confirmation(item_id: str, payload: ConfirmationApproveRequest | None = None, db: Session = Depends(get_db)) -> Confirmation:
    item = get_one(db, Confirmation, item_id)
    item.status = "approved"
    item.decision_json = {"decision": payload.decision if payload else {}}
    db.commit()
    db.refresh(item)
    return item


@router.post("/{item_id}/reject", response_model=ConfirmationRead)
def reject_confirmation(item_id: str, payload: ConfirmationRejectRequest | None = None, db: Session = Depends(get_db)) -> Confirmation:
    item = get_one(db, Confirmation, item_id)
    item.status = "rejected"
    item.decision_json = {"reason": payload.reason if payload else None}
    db.commit()
    db.refresh(item)
    return item


@router.post("/{item_id}/edit", response_model=ConfirmationRead)
def edit_confirmation(item_id: str, payload: ConfirmationEditRequest, db: Session = Depends(get_db)) -> Confirmation:
    item = get_one(db, Confirmation, item_id)
    item.status = "edited"
    item.decision_json = {"decision": payload.decision, "edited_payload": payload.edited_payload}
    if payload.edited_payload:
        item.payload_json = {**item.payload_json, **payload.edited_payload}
    db.commit()
    db.refresh(item)
    return item
