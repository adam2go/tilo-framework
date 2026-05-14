from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from tilo.models import Artifact, Confirmation, Run, Task
from tilo.services.trace.recorder import TraceRecorder


class ConfirmationService:
    def __init__(self, db: Session, trace: TraceRecorder):
        self.db = db
        self.trace = trace

    def create_for_artifact(self, task: Task, run: Run, artifact: Artifact) -> list[Confirmation]:
        confirmations: list[Confirmation] = []
        action_refs = self._collect_action_refs(artifact.schema_json)
        for block_id, action in action_refs:
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
                    "artifact_block_id": block_id,
                    "artifact_action_id": action.get("id"),
                    **(action.get("payload") or {}),
                },
            )
            confirmations.append(confirmation)

        self.db.add_all(confirmations)
        self.db.flush()
        confirmation_by_action_ref = {
            (confirmation.payload_json.get("artifact_block_id"), confirmation.payload_json.get("artifact_action_id")): confirmation.id
            for confirmation in confirmations
        }
        self._attach_confirmation_ids(artifact.schema_json, confirmation_by_action_ref)
        if confirmations:
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
            output_json={
                "count": len(confirmations),
                "artifact_action_ids": [action.get("id") for _, action in action_refs if action.get("confirmation_required")],
            },
        )
        return confirmations

    def _collect_action_refs(self, schema_json: dict) -> list[tuple[str | None, dict]]:
        refs: list[tuple[str | None, dict]] = [(None, action) for action in schema_json.get("actions", [])]
        for block in schema_json.get("blocks", []):
            for action in block.get("actions", []):
                refs.append((block.get("id"), action))
        return refs

    def _attach_confirmation_ids(self, schema_json: dict, confirmation_by_action_ref: dict[tuple[str | None, str | None], str]) -> None:
        for action in schema_json.get("actions", []):
            confirmation_id = confirmation_by_action_ref.get((None, action.get("id")))
            if confirmation_id:
                action["confirmation_id"] = confirmation_id
        for block in schema_json.get("blocks", []):
            for action in block.get("actions", []):
                confirmation_id = confirmation_by_action_ref.get((block.get("id"), action.get("id")))
                if confirmation_id:
                    action["confirmation_id"] = confirmation_id
