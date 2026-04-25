from typing import Any

from pydantic import ValidationError

from app.models import Memory, Run, Task
from app.schemas.artifact import ArtifactSpecV1


class ArtifactValidationError(ValueError):
    pass


class ArtifactTypeDetector:
    def detect(self, message: str) -> str:
        text = message.lower()
        if any(word in text for word in ["contract", "clause", "agreement", "nda", "合同", "条款"]):
            return "contract_review"
        if any(word in text for word in ["sales", "customer", "crm", "follow", "客户", "跟进"]):
            return "dashboard"
        if any(word in text for word in ["competitor", "competitive", "market", "竞品", "竞争"]):
            return "table"
        return "document"


class ArtifactSpecBuilder:
    def build(
        self,
        artifact_type: str,
        task: Task,
        run: Run,
        memories: list[Memory],
        tool_outputs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        memory_refs = [memory.id for memory in memories]
        memory_contents = [memory.content for memory in memories]
        if artifact_type == "contract_review":
            spec = ArtifactSpecV1(
                artifact_type="contract_review",
                title="Contract Review",
                blocks=[
                    {
                        "id": "summary",
                        "type": "card",
                        "title": "Summary",
                        "data": {
                            "title": "Summary",
                            "content": "The contract needs review around payment timing, liability, termination, and data handling.",
                        },
                    },
                    {
                        "id": "risk_1",
                        "type": "risk_item",
                        "title": "Liability",
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
                        "title": "Termination",
                        "data": {
                            "clause": "Termination",
                            "risk_level": "medium",
                            "issue": "Termination rights are not explicit enough for material breach.",
                            "suggested_revision": "Add a cure period and immediate termination for uncured material breach.",
                        },
                    },
                ],
                actions=[
                    {
                        "id": "approve_liability_revision",
                        "label": "Approve liability revision",
                        "action_type": "confirm",
                        "confirmation_required": True,
                        "payload": {
                            "risk_level": "high",
                            "operation": "propose_revision",
                            "target": "risk_1",
                        },
                    }
                ],
                provenance=[{"type": "task", "id": task.id, "label": task.title}],
                memory_refs=memory_refs,
                run_id=run.id,
            )
            return spec.model_dump(mode="json")

        if artifact_type == "dashboard":
            spec = ArtifactSpecV1(
                artifact_type="dashboard",
                title="Sales Follow-up Dashboard",
                blocks=[
                    {"id": "metric_1", "type": "metric", "data": {"label": "Hot accounts", "value": 3}},
                    {"id": "metric_2", "type": "metric", "data": {"label": "Projected pipeline", "value": "$84k"}},
                    {
                        "id": "recommendations",
                        "type": "list",
                        "title": "Recommended next actions",
                        "data": {
                            "items": [
                                "Follow up with Acme about procurement timeline.",
                                "Send renewal summary to Northstar.",
                                "Ask Finch Labs to confirm security review owner.",
                            ]
                        },
                    },
                ],
                actions=[
                    {
                        "id": "approve_sales_followup",
                        "label": "Approve sales follow-up",
                        "action_type": "confirm",
                        "confirmation_required": True,
                        "payload": {"customer": "Acme", "operation": "send_followup", "risk_level": "medium"},
                    }
                ],
                provenance=[{"type": "task", "id": task.id, "label": task.title}],
                memory_refs=memory_refs,
                run_id=run.id,
            )
            return spec.model_dump(mode="json")

        if artifact_type == "table":
            spec = ArtifactSpecV1(
                artifact_type="table",
                title="Competitive Analysis",
                blocks=[
                    {
                        "id": "comparison",
                        "type": "table",
                        "title": "Comparison",
                        "data": {
                            "columns": [
                                {"key": "company", "label": "Company"},
                                {"key": "positioning", "label": "Positioning"},
                                {"key": "strength", "label": "Strength"},
                                {"key": "gap", "label": "Gap"},
                            ],
                            "rows": [
                                {
                                    "company": "Competitor A",
                                    "positioning": "Enterprise workflow AI",
                                    "strength": "Integrations",
                                    "gap": "Weak artifact UX",
                                },
                                {
                                    "company": "Competitor B",
                                    "positioning": "Memory layer",
                                    "strength": "Developer adoption",
                                    "gap": "Limited SaaS console",
                                },
                                {
                                    "company": "Tilo",
                                    "positioning": "Memory-native agent SaaS runtime",
                                    "strength": "End-to-end loop",
                                    "gap": "Early ecosystem",
                                },
                            ],
                        },
                    },
                    {
                        "id": "summary",
                        "type": "markdown",
                        "data": {"content": "Tilo should differentiate through artifact-first delivery and confirmed memory loops."},
                    },
                ],
                provenance=[{"type": "task", "id": task.id, "label": task.title}],
                memory_refs=memory_refs,
                run_id=run.id,
            )
            return spec.model_dump(mode="json")

        memory_note = f"\n\nRecalled memory: {memory_contents[0]}" if memory_contents else ""
        spec = ArtifactSpecV1(
            artifact_type="document",
            title="Agent Result",
            blocks=[
                {
                    "id": "summary",
                    "type": "markdown",
                    "data": {"content": f"Processed request: {task.input_message}{memory_note}"},
                }
            ],
            provenance=[{"type": "task", "id": task.id, "label": task.title}],
            memory_refs=memory_refs,
            run_id=run.id,
        )
        return spec.model_dump(mode="json")


class ArtifactValidator:
    def normalize_and_validate(self, schema: dict[str, Any]) -> dict[str, Any]:
        normalized = {
            "version": "artifact_spec.v1",
            "status": "ready",
            "actions": [],
            "provenance": [],
            "memory_refs": [],
            **schema,
        }
        try:
            spec = ArtifactSpecV1.model_validate(normalized)
        except ValidationError as exc:
            raise ArtifactValidationError(str(exc)) from exc
        return spec.model_dump(mode="json")
