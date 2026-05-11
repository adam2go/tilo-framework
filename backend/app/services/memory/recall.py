from dataclasses import dataclass
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models import Memory, MemoryRecallEvent, Task


@dataclass(frozen=True)
class MemoryRecallResult:
    memory: Memory
    score: float
    score_parts: dict[str, float]


def tokenize(text: str) -> set[str]:
    return {word.strip(".,!?;:()[]{}\"'").lower() for word in text.split() if len(word.strip(".,!?;:()[]{}\"'")) > 3}


class MemoryRecallPipeline:
    strategy = "hybrid_v0.2"

    def __init__(self, db: Session):
        self.db = db

    def recall(
        self,
        *,
        workspace_id: str,
        project_id: str | None,
        query: str,
        limit: int = 5,
        memory_type: str | None = None,
        run_id: str | None = None,
    ) -> list[MemoryRecallResult]:
        query_words = tokenize(query)
        candidates = self._candidate_memories(workspace_id, project_id, memory_type)
        scored = [self._score_memory(memory, query_words, project_id) for memory in candidates]
        scored.sort(key=lambda result: result.score, reverse=True)
        selected = scored[:limit]

        now = utcnow()
        for result in selected:
            result.memory.last_recalled_at = now
            result.memory.recall_count = (result.memory.recall_count or 0) + 1

        event = self._record_event(workspace_id, project_id, run_id, query, selected)
        self.db.flush()
        for result in selected:
            self.db.refresh(result.memory)
        if event:
            self.db.refresh(event)
        return selected

    def _candidate_memories(self, workspace_id: str, project_id: str | None, memory_type: str | None) -> list[Memory]:
        stmt = select(Memory).where(
            Memory.workspace_id == workspace_id,
            or_(Memory.status == "confirmed", Memory.is_confirmed.is_(True)),
        )
        if project_id:
            stmt = stmt.where(or_(Memory.project_id == project_id, Memory.project_id.is_(None)))
        else:
            stmt = stmt.where(Memory.project_id.is_(None))
        if memory_type:
            stmt = stmt.where(Memory.type == memory_type)
        return list(self.db.scalars(stmt).all())

    def _score_memory(self, memory: Memory, query_words: set[str], project_id: str | None) -> MemoryRecallResult:
        content_words = tokenize(memory.content)
        keyword_score = self._keyword_score(query_words, content_words)
        salience = self._bounded(memory.salience if memory.salience is not None else memory.confidence)
        recency_score = self._recency_score(memory)
        scope_score = self._scope_score(memory, project_id)
        semantic_score = self._semantic_score(memory, query_words)

        if semantic_score is None:
            score = keyword_score * 0.45 + salience * 0.25 + recency_score * 0.20 + scope_score * 0.10
            score_parts = {
                "keyword_score": keyword_score,
                "salience": salience,
                "recency_score": recency_score,
                "scope_score": scope_score,
            }
        else:
            score = semantic_score * 0.50 + keyword_score * 0.20 + salience * 0.15 + recency_score * 0.10 + scope_score * 0.05
            score_parts = {
                "semantic_score": semantic_score,
                "keyword_score": keyword_score,
                "salience": salience,
                "recency_score": recency_score,
                "scope_score": scope_score,
            }

        return MemoryRecallResult(memory=memory, score=round(score, 4), score_parts=score_parts)

    def _record_event(
        self,
        workspace_id: str,
        project_id: str | None,
        run_id: str | None,
        query: str,
        selected: list[MemoryRecallResult],
    ) -> MemoryRecallEvent:
        event = MemoryRecallEvent(
            workspace_id=workspace_id,
            project_id=project_id,
            run_id=run_id,
            query_text=query,
            retrieved_memory_ids=[result.memory.id for result in selected],
            scores_json={
                result.memory.id: {"score": result.score, **result.score_parts}
                for result in selected
            },
            strategy=self.strategy,
        )
        self.db.add(event)
        return event

    @staticmethod
    def _keyword_score(query_words: set[str], content_words: set[str]) -> float:
        if not query_words or not content_words:
            return 0.0
        return round(len(query_words & content_words) / len(query_words), 4)

    @staticmethod
    def _recency_score(memory: Memory) -> float:
        if not memory.created_at:
            return 0.5
        age_days = max((utcnow() - memory.created_at).days, 0)
        return round(1 / (1 + age_days / 30), 4)

    @staticmethod
    def _scope_score(memory: Memory, project_id: str | None) -> float:
        if project_id and memory.project_id == project_id:
            return 1.0
        if memory.project_id is None:
            return 0.75
        return 0.35

    @staticmethod
    def _semantic_score(memory: Memory, query_words: set[str]) -> float | None:
        _ = (memory, query_words)
        return None

    @staticmethod
    def _bounded(value: float | None) -> float:
        if value is None:
            return 0.5
        return round(max(0.0, min(float(value), 1.0)), 4)


class MemoryRecallService:
    def __init__(self, db: Session):
        self.db = db
        self.pipeline = MemoryRecallPipeline(db)

    def recall_for_task(self, task: Task, limit: int = 5, memory_type: str | None = None, run_id: str | None = None) -> list[Memory]:
        return [
            result.memory
            for result in self.recall_for_task_with_scores(task, limit=limit, memory_type=memory_type, run_id=run_id)
        ]

    def recall_for_task_with_scores(
        self,
        task: Task,
        limit: int = 5,
        memory_type: str | None = None,
        run_id: str | None = None,
    ) -> list[MemoryRecallResult]:
        return self.pipeline.recall(
            workspace_id=task.workspace_id,
            project_id=task.project_id,
            query=task.input_message,
            limit=limit,
            memory_type=memory_type,
            run_id=run_id,
        )

    def recall_with_scores(
        self,
        *,
        workspace_id: str,
        project_id: str | None,
        query: str,
        limit: int = 5,
        memory_type: str | None = None,
        run_id: str | None = None,
    ) -> list[MemoryRecallResult]:
        return self.pipeline.recall(
            workspace_id=workspace_id,
            project_id=project_id,
            query=query,
            limit=limit,
            memory_type=memory_type,
            run_id=run_id,
        )


def recall_results_to_json(results: list[MemoryRecallResult]) -> list[dict[str, Any]]:
    return [
        {
            "memory_id": result.memory.id,
            "score": result.score,
            "score_parts": result.score_parts,
        }
        for result in results
    ]
