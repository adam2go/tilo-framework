from typing import Any

from pydantic import ValidationError

from app.models import Memory, Run, Task
from app.schemas.artifact import ArtifactSpecV1
from app.services.models.schemas import ContractReviewLLMData


class ArtifactValidationError(ValueError):
    pass


def _prefers_chinese(message: str) -> bool:
    return any(token in message for token in ["中文", "简体", "合同", "条款", "审查", "风险"])


def _default_contract_review_content(zh: bool, generation_mode: str) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    if zh:
        return (
            {
                "high_count": 2,
                "medium_count": 2,
                "low_count": 1,
                "confidence": "0.82",
                "status": "review_ready",
                "summary": "这份协议可以继续谈判，但责任限制、付款时间、终止权、保密义务和知识产权归属在签署前都需要有针对性的修订。",
                "generation_mode": generation_mode,
            },
            [
                {
                    "id": "risk_1",
                    "clause": "付款条款",
                    "risk_level": "medium",
                    "issue": "付款时间与发票收到时间绑定，但缺少清晰的争议处理窗口。",
                    "suggested_revision": "增加 10 个工作日的争议期，并要求无争议金额在 30 天内支付。",
                    "evidence": "条款约定收到发票后 30 天内付款，除非另有约定。",
                },
                {
                    "id": "risk_2",
                    "clause": "责任限制",
                    "risk_level": "high",
                    "issue": "责任可能没有上限，或只对一方有利。",
                    "suggested_revision": "增加双方适用的责任上限，并与过去 12 个月已支付费用挂钩。",
                    "evidence": "供应商责任排除没有明确对双方适用。",
                },
                {
                    "id": "risk_3",
                    "clause": "终止条款",
                    "risk_level": "medium",
                    "issue": "重大违约的终止权不够明确。",
                    "suggested_revision": "增加补救期，并允许对未补救的重大违约立即终止。",
                    "evidence": "条款允许便利终止，但没有清晰覆盖重大违约。",
                },
                {
                    "id": "risk_4",
                    "clause": "保密义务",
                    "risk_level": "low",
                    "issue": "保密义务的存续期间未明确。",
                    "suggested_revision": "增加三年存续期，并对商业秘密提供无限期保护。",
                    "evidence": "保密义务仅按法律要求存续。",
                },
                {
                    "id": "risk_5",
                    "clause": "知识产权归属",
                    "risk_level": "high",
                    "issue": "工作成果归属过宽，可能覆盖既有知识产权。",
                    "suggested_revision": "区分客户拥有的交付物、供应商背景 IP 和可复用 know-how。",
                    "evidence": "协议下创建或使用的全部材料都转让给客户。",
                },
            ],
            {
                "heading": "保守修订草案",
                "content": "任一方的累计责任应以索赔发生前十二个月内已支付或应支付费用为上限，但保密义务、数据滥用和付款义务除外。",
                "status": "draft",
                "highlights": ["双方责任上限", "重大违约补救期", "背景 IP 例外"],
            },
            {
                "content": "用户偏好保守的合同风险审查，并希望明确责任上限。",
                "memory_type": "preference",
                "confidence": 0.74,
            },
        )
    return (
        {
            "high_count": 2,
            "medium_count": 2,
            "low_count": 1,
            "confidence": "0.82",
            "status": "review_ready",
            "summary": "The agreement is negotiable, but liability, payment timing, termination, confidentiality, and IP ownership need targeted revisions before signing.",
            "generation_mode": generation_mode,
        },
        [
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
        ],
        {
            "heading": "Conservative revision draft",
            "content": "Each party's aggregate liability is capped at fees paid or payable in the twelve months preceding the claim, except for confidentiality, data misuse, and payment obligations.",
            "status": "draft",
            "highlights": ["Mutual liability cap", "Material breach cure period", "Background IP carve-out"],
        },
        {
            "content": "User prefers conservative contract risk review with explicit liability caps.",
            "memory_type": "preference",
            "confidence": 0.74,
        },
    )


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
        contract_llm_data: ContractReviewLLMData | None = None,
        generation_mode: str = "deterministic",
    ) -> dict[str, Any]:
        memory_refs = [memory.id for memory in memories]
        memory_contents = [memory.content for memory in memories]
        if artifact_type == "contract_review":
            zh = _prefers_chinese(task.input_message)
            risk_summary_data, risks, revision_draft, memory_candidate = _default_contract_review_content(zh, generation_mode)
            if contract_llm_data:
                risk_summary_data.update(
                    {
                        "high_count": contract_llm_data.risk_summary.high_count,
                        "medium_count": contract_llm_data.risk_summary.medium_count,
                        "low_count": contract_llm_data.risk_summary.low_count,
                        "summary": contract_llm_data.risk_summary.summary,
                        "confidence": "0.86",
                    }
                )
                risks = [risk.model_dump(mode="json") for risk in contract_llm_data.risks]
                revision_draft = {
                    "heading": contract_llm_data.revision_draft.heading,
                    "content": contract_llm_data.revision_draft.content,
                    "status": "draft",
                    "highlights": contract_llm_data.revision_draft.highlights,
                }
                memory_candidate = {
                    "content": contract_llm_data.memory_candidate.content,
                    "memory_type": contract_llm_data.memory_candidate.type,
                    "confidence": contract_llm_data.memory_candidate.confidence,
                }
            spec = ArtifactSpecV1(
                artifact_type="contract_review",
                title="合同审查" if zh else "Contract Review",
                blocks=[
                    {
                        "id": "risk_summary",
                        "type": "risk_summary",
                        "title": "风险摘要" if zh else "Risk Summary",
                        "data": risk_summary_data,
                        "state_binding": {"entity_type": "run", "entity_id": run.id, "field": "risk_summary"},
                    },
                    {
                        "id": "summary",
                        "type": "approval_card",
                        "title": "摘要" if zh else "Summary",
                        "data": {
                            "title": "摘要" if zh else "Summary",
                            "content": risk_summary_data["summary"],
                            "risk_level": "high",
                        },
                        "state_binding": {"entity_type": "run", "entity_id": run.id},
                        "actions": [
                            {
                                "id": "approve_summary",
                                "label": "批准审查方向" if zh else "Approve review direction",
                                "action_type": "approve",
                                "confirmation_required": True,
                                "payload": {"operation": "approve_contract_review", "risk_level": "high"},
                            },
                            {
                                "id": "reject_summary",
                                "label": "拒绝方向" if zh else "Reject direction",
                                "action_type": "reject",
                                "confirmation_required": False,
                                "payload": {"operation": "reject_contract_review"},
                            },
                        ],
                    },
                    {
                        "id": "risk_review",
                        "type": "risk_review_panel",
                        "title": "风险审查" if zh else "Risk Review",
                        "data": {"risks": risks},
                        "state_binding": {"entity_type": "run", "entity_id": run.id, "field": "risk_review"},
                        "actions": [
                            {
                                "id": "accept_risks",
                                "label": "接受风险审查" if zh else "Accept risk review",
                                "action_type": "approve",
                                "confirmation_required": False,
                                "payload": {"operation": "accept_risk_review"},
                            },
                            {
                                "id": "revise_risks",
                                "label": "请求修订" if zh else "Request revision",
                                "action_type": "regenerate",
                                "confirmation_required": False,
                                "payload": {"operation": "regenerate_risk_review"},
                            },
                        ],
                    },
                    {
                        "id": "editable_revision",
                        "type": "editable_document_preview",
                        "title": "可编辑修订草案" if zh else "Editable revision draft",
                        "data": revision_draft,
                        "actions": [
                            {
                                "id": "edit_liability_clause",
                                "label": "标记为待编辑" if zh else "Mark for editing",
                                "action_type": "edit",
                                "confirmation_required": False,
                                "payload": {"operation": "edit_clause", "target": "liability"},
                            }
                        ],
                    },
                    {
                        "id": "memory_candidate",
                        "type": "memory_candidate_card",
                        "title": "潜在记忆" if zh else "Potential memory",
                        "data": memory_candidate,
                        "actions": [
                            {
                                "id": "create_contract_memory",
                                "label": "保存为记忆候选" if zh else "Save as memory candidate",
                                "action_type": "create_memory",
                                "confirmation_required": False,
                                "payload": {
                                    "content": memory_candidate["content"],
                                    "type": memory_candidate["memory_type"],
                                },
                            }
                        ],
                    },
                ],
                actions=[
                    {
                        "id": "approve_liability_revision",
                        "label": "批准责任条款修订" if zh else "Approve liability revision",
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
