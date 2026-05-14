from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from tilo.api.deps import apply_update, get_one
from tilo.core.database import get_db
from tilo.models import Memory, MemoryRecallEvent, MemoryWriteEvent, Task
from tilo.schemas import (
    MemoryCreate,
    MemoryEditRequest,
    MemoryRead,
    MemoryRecallEventRead,
    MemoryRecallRequest,
    MemoryRejectRequest,
    MemoryWriteEventRead,
)
from tilo.services.memory.recall import MemoryRecallService
from tilo.services.memory.writer import MemoryWriter

router = APIRouter(prefix="/api/memories", tags=["memories"])


@router.get("", response_model=list[MemoryRead])
def list_memories(
    workspace_id: str,
    project_id: str | None = None,
    type: str | None = None,
    status: str | None = None,
    include_archived: bool = False,
    db: Session = Depends(get_db),
) -> Sequence[Memory]:
    stmt = select(Memory).where(Memory.workspace_id == workspace_id)
    if project_id:
        stmt = stmt.where(Memory.project_id == project_id)
    if type:
        stmt = stmt.where(Memory.type == type)
    if status:
        stmt = stmt.where(Memory.status == status)
    elif not include_archived:
        stmt = stmt.where(Memory.status != "archived")
    return db.scalars(stmt.order_by(Memory.created_at.desc())).all()


@router.post("", response_model=MemoryRead)
def create_memory(payload: MemoryCreate, db: Session = Depends(get_db)) -> Memory:
    data = payload.model_dump()
    data["is_confirmed"] = payload.status == "confirmed" or payload.is_confirmed
    if data["is_confirmed"]:
        data["status"] = "confirmed"
    if not data.get("scope_id"):
        data["scope_id"] = payload.project_id or payload.workspace_id
    if payload.project_id and payload.scope_type == "workspace":
        data["scope_type"] = "project"
    item = Memory(**data)
    db.add(item)
    db.flush()
    MemoryWriter(db).record_event(
        workspace_id=item.workspace_id,
        project_id=item.project_id,
        memory_id=item.id,
        run_id=item.source_run_id,
        event_type="confirmed" if item.is_confirmed else "candidate_created",
        payload_json={"content": item.content, "type": item.type, "source_type": item.source_type},
    )
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=MemoryRead)
def update_memory(item_id: str, payload: dict[str, Any], db: Session = Depends(get_db)) -> Memory:
    item = apply_update(get_one(db, Memory, item_id), payload)
    MemoryWriter(db).record_event(
        workspace_id=item.workspace_id,
        project_id=item.project_id,
        memory_id=item.id,
        run_id=item.source_run_id,
        event_type="edited",
        payload_json=payload,
    )
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}")
def delete_memory(item_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    item = get_one(db, Memory, item_id)
    MemoryWriter(db).archive(item)
    db.commit()
    return {"status": "archived"}


@router.post("/recall", response_model=list[MemoryRead])
def recall_memories(payload: MemoryRecallRequest, db: Session = Depends(get_db)) -> Sequence[Memory]:
    task = Task(workspace_id=payload.workspace_id, project_id=payload.project_id, title=payload.query[:80], input_message=payload.query)
    memories = MemoryRecallService(db).recall_for_task(task, payload.limit, payload.type)
    db.commit()
    return memories


@router.post("/{item_id}/confirm", response_model=MemoryRead)
def confirm_memory(item_id: str, db: Session = Depends(get_db)) -> Memory:
    item = get_one(db, Memory, item_id)
    MemoryWriter(db).confirm(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/{item_id}/reject", response_model=MemoryRead)
def reject_memory(item_id: str, payload: MemoryRejectRequest, db: Session = Depends(get_db)) -> Memory:
    item = get_one(db, Memory, item_id)
    MemoryWriter(db).reject(item, payload.reason)
    db.commit()
    db.refresh(item)
    return item


@router.post("/{item_id}/edit", response_model=MemoryRead)
def edit_memory(item_id: str, payload: MemoryEditRequest, db: Session = Depends(get_db)) -> Memory:
    item = get_one(db, Memory, item_id)
    updates = payload.model_dump(exclude_none=True)
    MemoryWriter(db).edit(item, updates)
    db.commit()
    db.refresh(item)
    return item


@router.get("/events/write", response_model=list[MemoryWriteEventRead])
def list_memory_write_events(workspace_id: str, memory_id: str | None = None, db: Session = Depends(get_db)) -> Sequence[MemoryWriteEvent]:
    stmt = select(MemoryWriteEvent).where(MemoryWriteEvent.workspace_id == workspace_id)
    if memory_id:
        stmt = stmt.where(MemoryWriteEvent.memory_id == memory_id)
    return db.scalars(stmt.order_by(MemoryWriteEvent.created_at.desc())).all()


@router.get("/events/recall", response_model=list[MemoryRecallEventRead])
def list_memory_recall_events(workspace_id: str, run_id: str | None = None, db: Session = Depends(get_db)) -> Sequence[MemoryRecallEvent]:
    stmt = select(MemoryRecallEvent).where(MemoryRecallEvent.workspace_id == workspace_id)
    if run_id:
        stmt = stmt.where(MemoryRecallEvent.run_id == run_id)
    return db.scalars(stmt.order_by(MemoryRecallEvent.created_at.desc())).all()
