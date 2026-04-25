from sqlalchemy.orm import Session

from app.models import Artifact, Memory, Run, Task
from app.services.trace.recorder import TraceRecorder
from app.services.memory.writer import MemoryWriter


class MemoryExtractionService:
    def __init__(self, db: Session, trace: TraceRecorder):
        self.db = db
        self.trace = trace

    def extract_candidates(self, task: Task, run: Run, artifact: Artifact) -> list[Memory]:
        content = {
            "contract_review": "User is interested in careful contract risk review and prefers explicit approval for high-risk revisions.",
            "dashboard": "User cares about sales follow-up prioritization and wants approvals before outbound actions.",
            "table": "User is researching competitors and values structured comparison tables.",
        }.get(artifact.type, f"User asked Tilo to process: {task.title}")
        memory = MemoryWriter(self.db).create_candidate(
            workspace_id=task.workspace_id,
            project_id=task.project_id,
            run_id=run.id,
            memory_type="task_experience",
            content=content,
            confidence=0.72,
            salience=0.55,
            source_artifact_id=artifact.id,
            reason="Extracted from completed run artifact for future task personalization.",
        )
        self.db.commit()
        self.db.refresh(memory)
        self.trace.record(
            run.id,
            "extract_memory",
            "Extract memory candidates",
            "Created one unconfirmed memory candidate.",
            output_json={"memory_id": memory.id},
        )
        return [memory]
