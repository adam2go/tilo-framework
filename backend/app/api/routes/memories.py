from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import apply_update, get_one
from app.core.database import get_db
from app.models import Memory, Task
from app.schemas import MemoryCreate, MemoryRead, MemoryRecallRequest
from app.services.memory.recall import MemoryRecallService

router = APIRouter(prefix="/api/memories", tags=["memories"])


@router.get("", response_model=list[MemoryRead])
def list_memories(workspace_id: str, project_id: str | None = None, type: str | None = None, db: Session = Depends(get_db)) -> Sequence[Memory]:
    stmt = select(Memory).where(Memory.workspace_id == workspace_id)
    if project_id:
        stmt = stmt.where(Memory.project_id == project_id)
    if type:
        stmt = stmt.where(Memory.type == type)
    return db.scalars(stmt.order_by(Memory.created_at.desc())).all()


@router.post("", response_model=MemoryRead)
def create_memory(payload: MemoryCreate, db: Session = Depends(get_db)) -> Memory:
    item = Memory(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=MemoryRead)
def update_memory(item_id: str, payload: dict[str, Any], db: Session = Depends(get_db)) -> Memory:
    item = apply_update(get_one(db, Memory, item_id), payload)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}")
def delete_memory(item_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    item = get_one(db, Memory, item_id)
    db.delete(item)
    db.commit()
    return {"status": "deleted"}


@router.post("/recall", response_model=list[MemoryRead])
def recall_memories(payload: MemoryRecallRequest, db: Session = Depends(get_db)) -> Sequence[Memory]:
    task = Task(workspace_id=payload.workspace_id, project_id=payload.project_id, title=payload.query[:80], input_message=payload.query)
    return MemoryRecallService(db).recall_for_task(task, payload.limit, payload.type)


@router.post("/{item_id}/confirm", response_model=MemoryRead)
def confirm_memory(item_id: str, db: Session = Depends(get_db)) -> Memory:
    item = get_one(db, Memory, item_id)
    item.is_confirmed = True
    db.commit()
    db.refresh(item)
    return item
