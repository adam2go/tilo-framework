from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import apply_update, get_one
from app.core.database import get_db
from app.models import Artifact
from app.schemas import ArtifactCreate, ArtifactRead

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


@router.get("", response_model=list[ArtifactRead])
def list_artifacts(workspace_id: str, project_id: str | None = None, task_id: str | None = None, db: Session = Depends(get_db)) -> Sequence[Artifact]:
    stmt = select(Artifact).where(Artifact.workspace_id == workspace_id)
    if project_id:
        stmt = stmt.where(Artifact.project_id == project_id)
    if task_id:
        stmt = stmt.where(Artifact.task_id == task_id)
    return db.scalars(stmt.order_by(Artifact.created_at.desc())).all()


@router.get("/{item_id}", response_model=ArtifactRead)
def read_artifact(item_id: str, db: Session = Depends(get_db)) -> Artifact:
    return get_one(db, Artifact, item_id)


@router.patch("/{item_id}", response_model=ArtifactRead)
def update_artifact(item_id: str, payload: dict[str, Any], db: Session = Depends(get_db)) -> Artifact:
    item = apply_update(get_one(db, Artifact, item_id), payload)
    db.commit()
    db.refresh(item)
    return item


@router.post("/{item_id}/versions", response_model=ArtifactRead)
def create_artifact_version(item_id: str, payload: ArtifactCreate, db: Session = Depends(get_db)) -> Artifact:
    original = get_one(db, Artifact, item_id)
    item = Artifact(**payload.model_dump(exclude={"version"}), version=original.version + 1)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
