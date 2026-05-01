from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Artifact, Confirmation, Memory
from app.services.interactions.events import UIInteractionEventService
from app.services.interaction_policy.schemas import InteractionContext, InteractionDecision
from app.services.interaction_policy.service import InteractionPolicyService


class AgentContextBuilder:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build(
        self,
        *,
        app_id: str,
        workspace_id: str,
        project_id: str | None = None,
        artifact_id: str | None = None,
        policy_context: InteractionContext | None = None,
    ) -> dict[str, Any]:
        artifact = self.db.get(Artifact, artifact_id) if artifact_id else self._latest_artifact(workspace_id, project_id)
        last_policy_decision = InteractionPolicyService().evaluate_for_app(app_id, policy_context) if policy_context else None
        return {
            "app_id": app_id,
            "workspace_id": workspace_id,
            "project_id": project_id,
            "recent_ui_observations": [
                {
                    "id": event.id,
                    "event_type": event.event_type,
                    "artifact_id": event.artifact_id,
                    "run_id": event.run_id,
                    "payload": event.payload_json,
                    "created_at": event.created_at.isoformat(),
                }
                for event in UIInteractionEventService(self.db).recent_for_context(workspace_id=workspace_id, project_id=project_id)
            ],
            "pending_confirmations": [
                {"id": item.id, "type": item.type, "title": item.title, "run_id": item.run_id}
                for item in self._pending_confirmations(workspace_id)
            ],
            "confirmed_memories": [
                {"id": item.id, "type": item.type, "content": item.content, "confidence": item.confidence}
                for item in self._confirmed_memories(workspace_id, project_id)
            ],
            "active_artifact_summary": self._artifact_summary(artifact),
            "last_policy_decision": last_policy_decision.model_dump() if isinstance(last_policy_decision, InteractionDecision) else None,
            "budget_counters_source": "caller_supplied_round_1_5",
        }

    def _latest_artifact(self, workspace_id: str, project_id: str | None) -> Artifact | None:
        stmt = select(Artifact).where(Artifact.workspace_id == workspace_id)
        if project_id:
            stmt = stmt.where(Artifact.project_id == project_id)
        return self.db.scalars(stmt.order_by(Artifact.created_at.desc())).first()

    def _pending_confirmations(self, workspace_id: str) -> list[Confirmation]:
        stmt = select(Confirmation).where(Confirmation.workspace_id == workspace_id, Confirmation.status == "pending")
        return list(self.db.scalars(stmt.order_by(Confirmation.created_at.desc()).limit(5)).all())

    def _confirmed_memories(self, workspace_id: str, project_id: str | None) -> list[Memory]:
        stmt = select(Memory).where(Memory.workspace_id == workspace_id, Memory.status == "confirmed", Memory.is_confirmed.is_(True))
        if project_id:
            stmt = stmt.where(Memory.project_id == project_id)
        return list(self.db.scalars(stmt.order_by(Memory.created_at.desc()).limit(5)).all())

    def _artifact_summary(self, artifact: Artifact | None) -> dict[str, Any] | None:
        if not artifact:
            return None
        blocks = artifact.schema_json.get("blocks", [])
        risk_summary = next((block.get("data", {}) for block in blocks if block.get("id") == "risk_summary"), {})
        return {
            "id": artifact.id,
            "type": artifact.type,
            "title": artifact.title,
            "run_id": artifact.run_id,
            "status": artifact.schema_json.get("status"),
            "block_count": len(blocks),
            "risk_summary": risk_summary,
        }
