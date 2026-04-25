from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import apply_update, get_one
from app.core.database import get_db
from app.models import Project
from app.schemas import ProjectCreate, ProjectRead

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
def list_projects(workspace_id: str, db: Session = Depends(get_db)) -> Sequence[Project]:
    return db.scalars(select(Project).where(Project.workspace_id == workspace_id).order_by(Project.created_at)).all()


@router.post("", response_model=ProjectRead)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    item = Project(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=ProjectRead)
def read_project(item_id: str, db: Session = Depends(get_db)) -> Project:
    return get_one(db, Project, item_id)


@router.patch("/{item_id}", response_model=ProjectRead)
def update_project(item_id: str, payload: dict[str, Any], db: Session = Depends(get_db)) -> Project:
    item = apply_update(get_one(db, Project, item_id), payload)
    db.commit()
    db.refresh(item)
    return item
