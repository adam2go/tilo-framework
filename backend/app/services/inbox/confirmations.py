from sqlalchemy.orm import Session

from app.models import Artifact, Confirmation, Run, Task
from app.services.trace.recorder import TraceRecorder


class ConfirmationService:
    def __init__(self, db: Session, trace: TraceRecorder):
        self.db = db
        self.trace = trace

    def create_for_artifact(self, task: Task, run: Run, artifact: Artifact) -> list[Confirmation]:
        confirmations: list[Confirmation] = []
        if artifact.type == "contract_review":
            confirmations.append(
                Confirmation(
                    workspace_id=task.workspace_id,
                    task_id=task.id,
                    run_id=run.id,
                    type="risk_approval",
                    title="Approve liability revision",
                    description="High-risk liability clause should be revised before sending.",
                    payload_json={"artifact_id": artifact.id, "risk_level": "high", "action": "propose_revision"},
                )
            )
        elif artifact.type == "dashboard":
            confirmations.append(
                Confirmation(
                    workspace_id=task.workspace_id,
                    task_id=task.id,
                    run_id=run.id,
                    type="send_followup",
                    title="Approve sales follow-up",
                    description="Approve the recommended follow-up message before sending.",
                    payload_json={"artifact_id": artifact.id, "customer": "Acme", "risk_level": "medium"},
                )
            )

        self.db.add_all(confirmations)
        self.db.commit()
        for confirmation in confirmations:
            self.db.refresh(confirmation)
        self.trace.record(
            run.id,
            "ask_confirmation",
            "Create confirmations",
            f"Created {len(confirmations)} confirmation item(s).",
            output_json={"count": len(confirmations)},
        )
        return confirmations
