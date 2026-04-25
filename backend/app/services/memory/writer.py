from typing import Any

from sqlalchemy.orm import Session

from app.models import Memory, MemoryWriteEvent


class MemoryWriter:
    def __init__(self, db: Session):
        self.db = db

    def create_candidate(
        self,
        *,
        workspace_id: str,
        project_id: str | None,
        run_id: str | None,
        content: str,
        memory_type: str = "task_experience",
        confidence: float = 0.72,
        salience: float = 0.5,
        source_artifact_id: str | None = None,
        reason: str = "",
        structured_payload: dict[str, Any] | None = None,
    ) -> Memory:
        memory = Memory(
            workspace_id=workspace_id,
            project_id=project_id,
            scope_type="project" if project_id else "workspace",
            scope_id=project_id or workspace_id,
            type=memory_type,
            content=content,
            source_type="run",
            source_id=run_id,
            source_run_id=run_id,
            confidence=confidence,
            salience=salience,
            status="candidate",
            is_confirmed=False,
            structured_payload={
                "reason": reason,
                "source_artifact_id": source_artifact_id,
                **(structured_payload or {}),
            },
        )
        self.db.add(memory)
        self.db.flush()
        self.record_event(
            workspace_id=workspace_id,
            project_id=project_id,
            memory_id=memory.id,
            run_id=run_id,
            event_type="candidate_created",
            payload_json={
                "content": content,
                "type": memory_type,
                "confidence": confidence,
                "salience": salience,
                "reason": reason,
                "source_artifact_id": source_artifact_id,
            },
        )
        return memory

    def confirm(self, memory: Memory) -> Memory:
        memory.is_confirmed = True
        memory.status = "confirmed"
        self.record_event(
            workspace_id=memory.workspace_id,
            project_id=memory.project_id,
            memory_id=memory.id,
            run_id=memory.source_run_id,
            event_type="confirmed",
            payload_json={"content": memory.content, "type": memory.type},
        )
        return memory

    def reject(self, memory: Memory, reason: str | None = None) -> Memory:
        memory.is_confirmed = False
        memory.status = "rejected"
        self.record_event(
            workspace_id=memory.workspace_id,
            project_id=memory.project_id,
            memory_id=memory.id,
            run_id=memory.source_run_id,
            event_type="rejected",
            payload_json={"reason": reason},
        )
        return memory

    def edit(self, memory: Memory, payload: dict[str, Any]) -> Memory:
        for field in ("content", "type", "scope_type", "scope_id", "salience", "confidence", "structured_payload"):
            if field in payload:
                setattr(memory, field, payload[field])
        if "status" in payload:
            memory.status = payload["status"]
            memory.is_confirmed = payload["status"] == "confirmed"
        if payload.get("is_confirmed") is True:
            memory.status = "confirmed"
            memory.is_confirmed = True
        elif payload.get("is_confirmed") is False and memory.status == "confirmed":
            memory.status = "candidate"
            memory.is_confirmed = False
        self.record_event(
            workspace_id=memory.workspace_id,
            project_id=memory.project_id,
            memory_id=memory.id,
            run_id=memory.source_run_id,
            event_type="edited",
            payload_json=payload,
        )
        return memory

    def archive(self, memory: Memory) -> Memory:
        memory.status = "archived"
        memory.is_confirmed = False
        self.record_event(
            workspace_id=memory.workspace_id,
            project_id=memory.project_id,
            memory_id=memory.id,
            run_id=memory.source_run_id,
            event_type="archived",
            payload_json={"content": memory.content},
        )
        return memory

    def record_event(
        self,
        *,
        workspace_id: str,
        project_id: str | None,
        memory_id: str | None,
        run_id: str | None,
        event_type: str,
        payload_json: dict[str, Any],
    ) -> MemoryWriteEvent:
        event = MemoryWriteEvent(
            workspace_id=workspace_id,
            project_id=project_id,
            memory_id=memory_id,
            run_id=run_id,
            event_type=event_type,
            payload_json=payload_json,
        )
        self.db.add(event)
        return event
