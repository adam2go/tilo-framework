from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Agent, Project, Workspace
from app.schemas import BootstrapResponse

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/bootstrap", response_model=BootstrapResponse)
def bootstrap(db: Session = Depends(get_db)) -> dict[str, Any]:
    workspace = db.scalar(select(Workspace).limit(1))
    projects = db.scalars(select(Project).where(Project.workspace_id == workspace.id)).all() if workspace else []
    agents = db.scalars(select(Agent).where(Agent.workspace_id == workspace.id)).all() if workspace else []
    return {"workspace": workspace, "projects": projects, "agents": agents}
