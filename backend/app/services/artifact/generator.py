from typing import Any

from sqlalchemy.orm import Session

from app.models import Artifact, Memory, Run, Task
from app.services.trace.recorder import TraceRecorder


class ArtifactGenerator:
    def __init__(self, db: Session, trace: TraceRecorder):
        self.db = db
        self.trace = trace

    def generate(
        self,
        task: Task,
        run: Run,
        memories: list[Memory],
        tool_outputs: list[dict[str, Any]],
    ) -> Artifact:
        artifact_type = detect_artifact_type(task.input_message)
        schema = build_artifact_schema(artifact_type, task.input_message, [memory.content for memory in memories], tool_outputs)
        artifact = Artifact(
            workspace_id=task.workspace_id,
            project_id=task.project_id,
            task_id=task.id,
            run_id=run.id,
            type=artifact_type,
            title=schema["title"],
            schema_json=schema,
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        self.trace.record(
            run.id,
            "generate_artifact",
            "Generate artifact",
            f"Created {artifact_type} artifact.",
            output_json={"artifact_id": artifact.id, "title": artifact.title},
        )
        return artifact


def detect_artifact_type(message: str) -> str:
    text = message.lower()
    if any(word in text for word in ["contract", "clause", "agreement", "nda", "合同", "条款"]):
        return "contract_review"
    if any(word in text for word in ["sales", "customer", "crm", "follow", "客户", "跟进"]):
        return "dashboard"
    if any(word in text for word in ["competitor", "competitive", "market", "竞品", "竞争"]):
        return "table"
    return "document"


def build_artifact_schema(
    artifact_type: str,
    message: str,
    memories: list[str],
    tool_outputs: list[dict[str, Any]],
) -> dict[str, Any]:
    if artifact_type == "contract_review":
        return {
            "artifact_type": "contract_review",
            "title": "Contract Review",
            "blocks": [
                {"id": "summary", "type": "card", "data": {"title": "Summary", "content": "The contract needs review around payment timing, liability, termination, and data handling."}},
                {
                    "id": "risk_1",
                    "type": "risk_item",
                    "data": {
                        "clause": "Liability",
                        "risk_level": "high",
                        "issue": "Liability may be uncapped or one-sided.",
                        "suggested_revision": "Add a mutual liability cap tied to fees paid in the prior 12 months.",
                    },
                },
                {
                    "id": "risk_2",
                    "type": "risk_item",
                    "data": {
                        "clause": "Termination",
                        "risk_level": "medium",
                        "issue": "Termination rights are not explicit enough for material breach.",
                        "suggested_revision": "Add a cure period and immediate termination for uncured material breach.",
                    },
                },
                {"id": "confirm_1", "type": "confirmation_action", "data": {"title": "Approve high-risk revision proposal", "actions": ["approve", "reject"]}},
            ],
        }
    if artifact_type == "dashboard":
        return {
            "artifact_type": "dashboard",
            "title": "Sales Follow-up Dashboard",
            "blocks": [
                {"id": "metric_1", "type": "metric", "data": {"label": "Hot accounts", "value": 3}},
                {"id": "metric_2", "type": "metric", "data": {"label": "Projected pipeline", "value": "$84k"}},
                {
                    "id": "recommendations",
                    "type": "list",
                    "data": {
                        "items": [
                            "Follow up with Acme about procurement timeline.",
                            "Send renewal summary to Northstar.",
                            "Ask Finch Labs to confirm security review owner.",
                        ]
                    },
                },
            ],
        }
    if artifact_type == "table":
        return {
            "artifact_type": "table",
            "title": "Competitive Analysis",
            "blocks": [
                {
                    "id": "comparison",
                    "type": "table",
                    "data": {
                        "columns": [
                            {"key": "company", "label": "Company"},
                            {"key": "positioning", "label": "Positioning"},
                            {"key": "strength", "label": "Strength"},
                            {"key": "gap", "label": "Gap"},
                        ],
                        "rows": [
                            {"company": "Competitor A", "positioning": "Enterprise workflow AI", "strength": "Integrations", "gap": "Weak artifact UX"},
                            {"company": "Competitor B", "positioning": "Memory layer", "strength": "Developer adoption", "gap": "Limited SaaS console"},
                            {"company": "Tilo", "positioning": "Memory-native agent SaaS runtime", "strength": "End-to-end loop", "gap": "Early ecosystem"},
                        ],
                    },
                },
                {"id": "summary", "type": "markdown", "data": {"content": "Tilo should differentiate through artifact-first delivery and confirmed memory loops."}},
            ],
        }
    memory_note = f"\n\nRecalled memory: {memories[0]}" if memories else ""
    return {
        "artifact_type": "document",
        "title": "Agent Result",
        "blocks": [{"id": "summary", "type": "markdown", "data": {"content": f"Processed request: {message}{memory_note}"}}],
    }
