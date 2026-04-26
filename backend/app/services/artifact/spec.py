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
                        "id": "risk_summary",
                        "type": "risk_summary",
                        "title": "Risk Summary",
                        "data": {
                            "high_count": 2,
                            "medium_count": 2,
                            "low_count": 1,
                            "confidence": "0.82",
                            "status": "review_ready",
                            "summary": "The agreement is negotiable, but liability, payment timing, termination, confidentiality, and IP ownership need targeted revisions before signing.",
                        },
                        "state_binding": {"entity_type": "run", "entity_id": run.id, "field": "risk_summary"},
                    },
                    {
                        "id": "summary",
                        "type": "approval_card",
                        "title": "Summary",
                        "data": {
                            "title": "Summary",
                            "content": "The contract needs review around payment timing, liability, termination, and data handling.",
                            "risk_level": "high",
                        },
                        "state_binding": {"entity_type": "run", "entity_id": run.id},
                        "actions": [
                            {
                                "id": "approve_summary",
                                "label": "Approve review direction",
                                "action_type": "approve",
                                "confirmation_required": True,
                                "payload": {"operation": "approve_contract_review", "risk_level": "high"},
                            },
                            {
                                "id": "reject_summary",
                                "label": "Reject direction",
                                "action_type": "reject",
                                "confirmation_required": False,
                                "payload": {"operation": "reject_contract_review"},
                            },
                        ],
                    },
                    {
                        "id": "risk_review",
                        "type": "risk_review_panel",
                        "title": "Risk Review",
                        "data": {
                            "risks": [
                                {
                                    "id": "risk_1",
                                    "clause": "Payment terms",
                                    "risk_level": "medium",
                                    "issue": "Payment timing is tied to invoice receipt without a clear dispute window.",
                                    "suggested_revision": "Add a 10 business day dispute period and require undisputed amounts to be paid within 30 days.",
                                    "evidence": "Payment due within 30 days of receipt unless otherwise agreed.",
                                },
                                {
                                    "id": "risk_2",
                                    "clause": "Liability",
                                    "risk_level": "high",
                                    "issue": "Liability may be uncapped or one-sided.",
                                    "suggested_revision": "Add a mutual liability cap tied to fees paid in the prior 12 months.",
                                    "evidence": "Vendor liability exclusions do not clearly apply mutually.",
                                },
                                {
                                    "id": "risk_3",
                                    "clause": "Termination",
                                    "risk_level": "medium",
                                    "issue": "Termination rights are not explicit enough for material breach.",
                                    "suggested_revision": "Add a cure period and immediate termination for uncured material breach.",
                                    "evidence": "The clause allows termination for convenience but not material breach.",
                                },
                                {
                                    "id": "risk_4",
                                    "clause": "Confidentiality",
                                    "risk_level": "low",
                                    "issue": "Confidentiality survival period is not stated.",
                                    "suggested_revision": "Add a three-year survival period and indefinite protection for trade secrets.",
                                    "evidence": "Confidentiality obligations survive only as required by law.",
                                },
                                {
                                    "id": "risk_5",
                                    "clause": "IP ownership",
                                    "risk_level": "high",
                                    "issue": "Work product ownership is broad and could capture pre-existing IP.",
                                    "suggested_revision": "Separate customer-owned deliverables from vendor background IP and reusable know-how.",
                                    "evidence": "All materials created or used under the agreement transfer to customer.",
                                },
                            ]
                        },
                        "state_binding": {"entity_type": "run", "entity_id": run.id, "field": "risk_review"},
                        "actions": [
                            {
                                "id": "accept_risks",
                                "label": "Accept risk review",
                                "action_type": "approve",
                                "confirmation_required": False,
                                "payload": {"operation": "accept_risk_review"},
                            },
                            {
                                "id": "revise_risks",
                                "label": "Request revision",
                                "action_type": "regenerate",
                                "confirmation_required": False,
                                "payload": {"operation": "regenerate_risk_review"},
                            },
                        ],
                    },
                    {
                        "id": "editable_revision",
                        "type": "editable_document_preview",
                        "title": "Editable revision draft",
                        "data": {
                            "heading": "Conservative revision draft",
                            "content": "Each party's aggregate liability is capped at fees paid or payable in the twelve months preceding the claim, except for confidentiality, data misuse, and payment obligations.",
                            "status": "draft",
                            "highlights": [
                                "Mutual liability cap",
                                "Material breach cure period",
                                "Background IP carve-out",
                            ],
                        },
                        "actions": [
                            {
                                "id": "edit_liability_clause",
                                "label": "Mark for editing",
                                "action_type": "edit",
                                "confirmation_required": False,
                                "payload": {"operation": "edit_clause", "target": "liability"},
                            }
                        ],
                    },
                    {
                        "id": "memory_candidate",
                        "type": "memory_candidate_card",
                        "title": "Potential memory",
                        "data": {
                            "content": "User prefers conservative contract risk review with explicit liability caps.",
                            "memory_type": "preference",
                            "confidence": 0.74,
                        },
                        "actions": [
                            {
                                "id": "create_contract_memory",
                                "label": "Save as memory candidate",
                                "action_type": "create_memory",
                                "confirmation_required": False,
                                "payload": {
                                    "content": "User prefers conservative contract risk review with explicit liability caps.",
                                    "type": "preference",
                                },
                            }
                        ],
                    },
                ],
                actions=[
                    {
                        "id": "approve_liability_revision",
                        "label": "Approve liability revision",
                        "action_type": "approve",
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
                    {
                        "id": "pipeline_dashboard",
                        "type": "metric_dashboard",
                        "title": "Pipeline Snapshot",
                        "data": {
                            "metrics": [
                                {"label": "Hot accounts", "value": 3, "delta": "+1"},
                                {"label": "Projected pipeline", "value": "$84k", "delta": "+12%"},
                                {"label": "Pending decisions", "value": 2, "delta": "needs review"},
                            ],
                            "insights": [
                                "Acme has the strongest near-term procurement signal.",
                                "Northstar needs a renewal summary before legal review.",
                            ]
                        },
                        "state_binding": {"entity_type": "run", "entity_id": run.id, "field": "metrics"},
                    },
                    {
                        "id": "sales_actions",
                        "type": "action_queue",
                        "title": "Recommended next actions",
                        "data": {
                            "items": [
                                {"id": "acme", "title": "Follow up with Acme", "detail": "Ask about procurement timeline.", "status": "ready"},
                                {"id": "northstar", "title": "Send renewal summary", "detail": "Summarize renewal value before legal review.", "status": "waiting"},
                                {"id": "finch", "title": "Confirm security owner", "detail": "Ask Finch Labs to name the review owner.", "status": "ready"},
                            ]
                        },
                        "actions": [
                            {
                                "id": "select_acme_followup",
                                "label": "Select Acme follow-up",
                                "action_type": "select",
                                "confirmation_required": False,
                                "payload": {"customer": "Acme", "operation": "select_followup"},
                            }
                        ],
                    },
                    {
                        "id": "sales_tool_preview",
                        "type": "tool_call_preview",
                        "title": "Outbound action preview",
                        "data": {
                            "tool_name": "Mock Search",
                            "permission_level": "medium",
                            "summary": "Prepare a follow-up draft. External sending remains confirmation-gated.",
                        },
                    },
                ],
                actions=[
                    {
                        "id": "approve_sales_followup",
                        "label": "Approve sales follow-up",
                        "action_type": "approve",
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
                        "type": "comparison_matrix",
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
                        "actions": [
                            {
                                "id": "select_tilo_positioning",
                                "label": "Select Tilo positioning",
                                "action_type": "select",
                                "confirmation_required": False,
                                "payload": {"option": "Tilo", "criterion": "artifact-first delivery"},
                            }
                        ],
                    },
                    {
                        "id": "summary",
                        "type": "markdown",
                        "data": {"content": "Tilo should differentiate through artifact-first delivery and confirmed memory loops."},
                    },
                    {
                        "id": "competitive_next_steps",
                        "type": "action_queue",
                        "title": "Next steps",
                        "data": {
                            "items": [
                                {"id": "positioning", "title": "Refine public positioning", "detail": "Emphasize ROAM over static agent chat.", "status": "ready"},
                                {"id": "demo", "title": "Prepare screenshot demo", "detail": "Use ComparisonMatrix and ActionQueue.", "status": "ready"},
                            ]
                        },
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
