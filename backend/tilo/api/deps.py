from typing import Any, TypeVar

from fastapi import HTTPException
from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


def get_one(db: Session, model: type[ModelT], item_id: str) -> ModelT:
    item = db.get(model, item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return item


def apply_update(item: Any, patch: dict[str, Any]) -> Any:
    for key, value in patch.items():
        if hasattr(item, key) and key not in {"id", "created_at"}:
            setattr(item, key, value)
    return item
