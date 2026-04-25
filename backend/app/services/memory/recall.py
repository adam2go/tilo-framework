from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Memory, Task


class MemoryRecallService:
    def __init__(self, db: Session):
        self.db = db

    def recall_for_task(self, task: Task, limit: int = 5, memory_type: str | None = None) -> list[Memory]:
        words = {word.strip(".,!?;:").lower() for word in task.input_message.split() if len(word) > 3}
        stmt = select(Memory).where(Memory.workspace_id == task.workspace_id, Memory.is_confirmed.is_(True))
        if task.project_id:
            stmt = stmt.where((Memory.project_id == task.project_id) | (Memory.project_id.is_(None)))
        if memory_type:
            stmt = stmt.where(Memory.type == memory_type)

        scored: list[tuple[int, Memory]] = []
        for memory in self.db.scalars(stmt).all():
            content_words = set(memory.content.lower().split())
            score = len(words & content_words)
            if score > 0 or len(scored) < limit:
                scored.append((score, memory))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [memory for _, memory in scored[:limit]]
