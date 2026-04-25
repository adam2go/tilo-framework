from sqlalchemy.orm import Session

from app.models import Artifact, Memory, Run, Task
from app.services.trace.recorder import TraceRecorder


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
        memory = Memory(
            workspace_id=task.workspace_id,
            project_id=task.project_id,
            type="task_experience",
            content=content,
            source_type="run",
            source_id=run.id,
            confidence=0.72,
            is_confirmed=False,
        )
        self.db.add(memory)
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
