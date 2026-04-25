from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import apply_update, get_one
from app.core.database import get_db
from app.models import Tool
from app.schemas import ToolCreate, ToolInvokeRequest, ToolRead
from app.services.tools.invocation import ToolInvocationService

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("", response_model=list[ToolRead])
def list_tools(workspace_id: str, db: Session = Depends(get_db)) -> Sequence[Tool]:
    return db.scalars(select(Tool).where(Tool.workspace_id == workspace_id).order_by(Tool.created_at)).all()


@router.post("", response_model=ToolRead)
def create_tool(payload: ToolCreate, db: Session = Depends(get_db)) -> Tool:
    item = Tool(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=ToolRead)
def read_tool(item_id: str, db: Session = Depends(get_db)) -> Tool:
    return get_one(db, Tool, item_id)


@router.patch("/{item_id}", response_model=ToolRead)
def update_tool(item_id: str, payload: dict[str, Any], db: Session = Depends(get_db)) -> Tool:
    item = apply_update(get_one(db, Tool, item_id), payload)
    db.commit()
    db.refresh(item)
    return item


@router.post("/{item_id}/invoke")
def invoke_tool(item_id: str, payload: ToolInvokeRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    tool = get_one(db, Tool, item_id)
    return ToolInvocationService(db).invoke_direct(tool, payload.input)
