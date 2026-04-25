from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import apply_update, get_one
from app.core.database import get_db
from app.models import Skill
from app.schemas import SkillCreate, SkillRead

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


@router.get("/{item_id}", response_model=SkillRead)
def read_skill(item_id: str, db: Session = Depends(get_db)) -> Skill:
    return get_one(db, Skill, item_id)


@router.patch("/{item_id}", response_model=SkillRead)
def update_skill(item_id: str, payload: dict[str, Any], db: Session = Depends(get_db)) -> Skill:
    item = apply_update(get_one(db, Skill, item_id), payload)
    db.commit()
    db.refresh(item)
    return item
