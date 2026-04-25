from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import apply_update, get_one
from app.core.database import get_db
from app.models import Agent
from app.schemas import AgentCreate, AgentRead

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("", response_model=list[AgentRead])
def list_agents(workspace_id: str, db: Session = Depends(get_db)) -> Sequence[Agent]:
    return db.scalars(select(Agent).where(Agent.workspace_id == workspace_id).order_by(Agent.created_at)).all()


@router.post("", response_model=AgentRead)
def create_agent(payload: AgentCreate, db: Session = Depends(get_db)) -> Agent:
    item = Agent(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=AgentRead)
def read_agent(item_id: str, db: Session = Depends(get_db)) -> Agent:
    return get_one(db, Agent, item_id)


@router.patch("/{item_id}", response_model=AgentRead)
def update_agent(item_id: str, payload: dict[str, Any], db: Session = Depends(get_db)) -> Agent:
    item = apply_update(get_one(db, Agent, item_id), payload)
    db.commit()
    db.refresh(item)
    return item
