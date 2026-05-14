from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from tilo.api.deps import apply_update, get_one
from tilo.core.database import get_db
from tilo.models import Workspace
from tilo.schemas import WorkspaceCreate, WorkspaceRead

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceRead])
def list_workspaces(db: Session = Depends(get_db)) -> Sequence[Workspace]:
    return db.scalars(select(Workspace).order_by(Workspace.created_at)).all()


@router.post("", response_model=WorkspaceRead)
def create_workspace(payload: WorkspaceCreate, db: Session = Depends(get_db)) -> Workspace:
    item = Workspace(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=WorkspaceRead)
def read_workspace(item_id: str, db: Session = Depends(get_db)) -> Workspace:
    return get_one(db, Workspace, item_id)


@router.patch("/{item_id}", response_model=WorkspaceRead)
def update_workspace(item_id: str, payload: dict[str, Any], db: Session = Depends(get_db)) -> Workspace:
    item = apply_update(get_one(db, Workspace, item_id), payload)
    db.commit()
    db.refresh(item)
    return item
