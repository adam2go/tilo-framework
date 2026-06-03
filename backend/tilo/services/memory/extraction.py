"""Memory candidate extraction.

Phase 4 evolution: alongside the run's task-experience candidate, the
extractor consumes recent `UIInteractionEvent`s and asks
`BehaviourMemoryAnalyzer` for behaviour-derived candidates (repeated
rejects, repeated selects, editable-bound memory updates). Each
behavioural candidate is persisted as `source_type="ui_behaviour"` with
a `behaviour_signature` so subsequent runs can de-dup.
"""

from sqlalchemy.orm import Session

from tilo.models import Artifact, Memory, Run, Task, UIInteractionEvent
from tilo.services.memory.behaviour import (
    RECENT_EVENT_WINDOW,
    BehaviourMemoryAnalyzer,
)
from tilo.services.memory.writer import MemoryWriter
from tilo.services.trace.recorder import TraceRecorder


class MemoryExtractionService:
    def __init__(self, db: Session, trace: TraceRecorder):
        self.db = db
        self.trace = trace

    def extract_candidates(
        self,
        task: Task,
        run: Run,
        artifact: Artifact | None,
        *,
        recent_interaction_events: list[UIInteractionEvent] | None = None,
    ) -> list[Memory]:
        candidates: list[Memory] = []

        # 1. Existing "task experience" candidate based on the artifact type.
        #    These are routine memories — auto-confirm so the user doesn't
        #    get asked "Should I remember this?" on every single run.
        if artifact is not None:
            content = {
                "contract_review": "User is interested in careful contract risk review and prefers explicit approval for high-risk revisions.",
                "dashboard": "User cares about sales follow-up prioritization and wants approvals before outbound actions.",
                "table": "User is researching competitors and values structured comparison tables.",
            }.get(artifact.type, f"User asked Tilo to process: {task.title}")
            task_memory = MemoryWriter(self.db).create_candidate(
                workspace_id=task.workspace_id,
                project_id=task.project_id,
                run_id=run.id,
                memory_type="task_experience",
                content=content,
                confidence=0.72,
                source_artifact_id=artifact.id,
                reason="Extracted from completed run artifact for future task personalization.",
                auto_confirm=True,
            )
            candidates.append(task_memory)

        # 2. Behaviour-derived candidates from the recent UI interaction stream.
        #    Also auto-confirmed — these are derived from observed user
        #    behaviour patterns (repeated actions) so they're already
        #    evidence-backed.
        events = recent_interaction_events
        if events is None:
            events = self._load_recent_events(workspace_id=task.workspace_id, project_id=task.project_id)
        analyzer = BehaviourMemoryAnalyzer(self.db)
        behaviour_candidates = analyzer.analyse(
            workspace_id=task.workspace_id,
            project_id=task.project_id,
            events=events,
        )
        for behaviour in behaviour_candidates:
            memory = MemoryWriter(self.db).create_candidate(
                workspace_id=task.workspace_id,
                project_id=task.project_id,
                run_id=run.id,
                content=behaviour.content,
                memory_type=behaviour.memory_type,
                confidence=behaviour.confidence,
                salience=behaviour.salience,
                source_type="ui_behaviour",
                reason=behaviour.reason,
                structured_payload=behaviour.structured_payload,
                auto_confirm=True,
            )
            candidates.append(memory)

        self.db.commit()
        for memory in candidates:
            self.db.refresh(memory)

        self.trace.record(
            run.id,
            "extract_memory",
            "Extract memory candidates",
            (
                f"Created {len(candidates)} memory candidate(s): "
                f"{1 if artifact else 0} task experience, "
                f"{len(behaviour_candidates)} behaviour-derived."
            ),
            input_json={"recent_event_count": len(events)},
            output_json={
                "memory_ids": [m.id for m in candidates],
                "behaviour_candidates": [
                    {
                        "memory_id": memory.id,
                        "type": memory.type,
                        "rule": (memory.structured_payload or {}).get("rule"),
                        "behaviour_signature": (memory.structured_payload or {}).get("behaviour_signature"),
                    }
                    for memory in candidates
                    if memory.source_type == "ui_behaviour"
                ],
            },
        )
        return candidates

    def _load_recent_events(self, *, workspace_id: str, project_id: str | None) -> list[UIInteractionEvent]:
        query = self.db.query(UIInteractionEvent).filter(UIInteractionEvent.workspace_id == workspace_id)
        if project_id:
            query = query.filter(UIInteractionEvent.project_id == project_id)
        return list(
            query.order_by(UIInteractionEvent.created_at.desc()).limit(RECENT_EVENT_WINDOW).all()
        )
