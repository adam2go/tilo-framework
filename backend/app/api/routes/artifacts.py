from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import apply_update, get_one
from app.core.database import get_db
from app.models import Artifact
from app.schemas import ArtifactActionExecuteRequest, ArtifactActionResult, ArtifactCreate, ArtifactRead
from app.services.artifact.actions import ArtifactActionRuntime, ArtifactActionRuntimeError
from app.services.artifact.persistence import ArtifactPersistenceService
from app.services.artifact.spec import ArtifactValidationError, ArtifactValidator

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


@router.post("/{item_id}/actions/{action_id}", response_model=ArtifactActionResult)
def execute_artifact_action(
    item_id: str,
    action_id: str,
    payload: ArtifactActionExecuteRequest | None = None,
    db: Session = Depends(get_db),
) -> ArtifactActionResult:
    request = payload or ArtifactActionExecuteRequest()
    try:
        return ArtifactActionRuntime(db).execute(
            artifact_id=item_id,
            action_id=action_id,
            block_id=request.block_id,
            session_id=request.session_id,
            run_id=request.run_id,
            source=request.source,
            payload=request.payload,
            idempotency_key=request.idempotency_key,
        )
    except ArtifactActionRuntimeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.patch("/{item_id}", response_model=ArtifactRead)
def update_artifact(item_id: str, payload: dict[str, Any], db: Session = Depends(get_db)) -> Artifact:
    item = get_one(db, Artifact, item_id)
    if "schema_json" in payload:
        try:
            ArtifactPersistenceService(db).update_schema(item, payload["schema_json"])
        except ArtifactValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        payload = {key: value for key, value in payload.items() if key not in {"schema_json", "type", "title"}}
    item = apply_update(item, payload)
    db.commit()
    db.refresh(item)
    return item


@router.post("/{item_id}/versions", response_model=ArtifactRead)
def create_artifact_version(item_id: str, payload: ArtifactCreate, db: Session = Depends(get_db)) -> Artifact:
    original = get_one(db, Artifact, item_id)
    try:
        schema_json = ArtifactValidator().normalize_and_validate(payload.schema_json)
    except ArtifactValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    item = Artifact(**payload.model_dump(exclude={"version", "artifact_schema"}), schema_json=schema_json, version=original.version + 1)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
