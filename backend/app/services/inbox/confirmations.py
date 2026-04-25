from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models import Artifact, Confirmation, Run, Task
from app.services.trace.recorder import TraceRecorder


class ConfirmationService:
    def __init__(self, db: Session, trace: TraceRecorder):
        self.db = db
        self.trace = trace

    def create_for_artifact(self, task: Task, run: Run, artifact: Artifact) -> list[Confirmation]:
        confirmations: list[Confirmation] = []
        actions = artifact.schema_json.get("actions", [])
        for action in actions:
            if not action.get("confirmation_required"):
                continue
            confirmation = Confirmation(
                workspace_id=task.workspace_id,
                task_id=task.id,
                run_id=run.id,
                type=str(action.get("payload", {}).get("operation") or action.get("action_type") or "approval"),
                title=str(action.get("label") or "Approval required"),
                description=f"Review action from artifact {artifact.title}.",
                payload_json={
                    "artifact_id": artifact.id,
                    "artifact_action_id": action.get("id"),
                    **(action.get("payload") or {}),
                },
            )
            confirmations.append(confirmation)

        self.db.add_all(confirmations)
        self.db.flush()
        confirmation_by_action_id = {
            confirmation.payload_json.get("artifact_action_id"): confirmation.id
            for confirmation in confirmations
        }
        for action in actions:
            confirmation_id = confirmation_by_action_id.get(action.get("id"))
            if confirmation_id:
                action["confirmation_id"] = confirmation_id
        if confirmations:
            artifact.schema_json = {**artifact.schema_json, "actions": actions}
            flag_modified(artifact, "schema_json")
        self.db.commit()
        for confirmation in confirmations:
            self.db.refresh(confirmation)
        if confirmations:
            self.db.refresh(artifact)
        self.trace.record(
            run.id,
            "ask_confirmation",
            "Create confirmations",
            f"Created {len(confirmations)} confirmation item(s).",
            output_json={"count": len(confirmations), "artifact_action_ids": [action.get("id") for action in actions if action.get("confirmation_required")]},
        )
        return confirmations
