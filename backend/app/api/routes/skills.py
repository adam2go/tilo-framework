from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import apply_update, get_one
from app.core.database import get_db
from app.models import Skill, SkillCandidate
from app.schemas import (
    SkillCandidateCreate,
    SkillCandidateEditRequest,
    SkillCandidateRead,
    SkillCandidateRejectRequest,
    SkillCreate,
    SkillRead,
)
from app.services.improvement.candidates import SkillCandidateService

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("", response_model=list[SkillRead])
def list_skills(workspace_id: str, db: Session = Depends(get_db)) -> Sequence[Skill]:
    return db.scalars(select(Skill).where(Skill.workspace_id == workspace_id).order_by(Skill.created_at)).all()


@router.post("", response_model=SkillRead)
def create_skill(payload: SkillCreate, db: Session = Depends(get_db)) -> Skill:
    item = Skill(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/candidates", response_model=list[SkillCandidateRead])
def list_skill_candidates(
    workspace_id: str,
    status: str | None = None,
    db: Session = Depends(get_db),
) -> Sequence[SkillCandidate]:
    stmt = select(SkillCandidate).where(SkillCandidate.workspace_id == workspace_id)
    if status:
        stmt = stmt.where(SkillCandidate.status == status)
    return db.scalars(stmt.order_by(SkillCandidate.created_at.desc())).all()


@router.post("/candidates", response_model=SkillCandidateRead)
def create_skill_candidate(payload: SkillCandidateCreate, db: Session = Depends(get_db)) -> SkillCandidate:
    item = SkillCandidate(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/candidates/{item_id}", response_model=SkillCandidateRead)
def update_skill_candidate(item_id: str, payload: SkillCandidateEditRequest, db: Session = Depends(get_db)) -> SkillCandidate:
    item = apply_update(get_one(db, SkillCandidate, item_id), payload.model_dump(exclude_none=True))
    db.commit()
    db.refresh(item)
    return item


@router.post("/candidates/{item_id}/approve", response_model=SkillCandidateRead)
def approve_skill_candidate(item_id: str, db: Session = Depends(get_db)) -> SkillCandidate:
    item = get_one(db, SkillCandidate, item_id)
    SkillCandidateService(db).approve(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/candidates/{item_id}/reject", response_model=SkillCandidateRead)
def reject_skill_candidate(item_id: str, payload: SkillCandidateRejectRequest | None = None, db: Session = Depends(get_db)) -> SkillCandidate:
    item = get_one(db, SkillCandidate, item_id)
    SkillCandidateService(db).reject(item, payload.reason if payload else None)
    db.commit()
    db.refresh(item)
    return item


@router.post("/candidates/{item_id}/promote", response_model=SkillRead)
def promote_skill_candidate(item_id: str, db: Session = Depends(get_db)) -> Skill:
    item = get_one(db, SkillCandidate, item_id)
    skill = SkillCandidateService(db).promote(item)
    db.commit()
    db.refresh(skill)
    return skill


@router.get("/{item_id}", response_model=SkillRead)
def read_skill(item_id: str, db: Session = Depends(get_db)) -> Skill:
    return get_one(db, Skill, item_id)


@router.patch("/{item_id}", response_model=SkillRead)
def update_skill(item_id: str, payload: dict[str, Any], db: Session = Depends(get_db)) -> Skill:
    item = apply_update(get_one(db, Skill, item_id), payload)
    db.commit()
    db.refresh(item)
    return item
