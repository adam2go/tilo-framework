from typing import Any

from pydantic import ValidationError

from app.models import Memory, Run, Task
from app.schemas.artifact import ArtifactSpecV1
from app.services.models.schemas import ContractReviewLLMData


class ArtifactValidationError(ValueError):
    pass


def _prefers_chinese(message: str) -> bool:
    if any(token in message.lower() for token in ["return the contract review artifact in english", " in english", " english."]):
        return False
    return any(token in message for token in ["中文", "简体", "合同", "条款", "审查", "风险"])


def _is_problematic_ai_service_contract(message: str) -> bool:
    return "AI 客服系统定制开发与运维服务合同" in message or ("**8.1**" in message and "**8.2**" in message)


def _fixture_contract_review_content(zh: bool, generation_mode: str) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    if zh:
        return (
            {
                "high_count": 4,
                "medium_count": 4,
                "low_count": 0,
                "confidence": "0.88",
                "status": "review_ready",
                "summary": "我已完成整份 AI 客服系统服务合同审查。大部分问题可以继续自动整理，但 8.1 与 8.2 的责任上限和赔偿例外存在明显冲突，需要先确认修订方向。",
                "generation_mode": generation_mode,
            },
            [
                {
                    "id": "risk_liability_indemnity_conflict",
                    "clause": "8.1 / 8.2",
                    "risk_level": "high",
                    "issue": "8.1 看似设置乙方责任上限，但 8.2 将数据泄露、知识产权争议、监管处罚、模型输出错误、用户投诉、业务损失、间接损失和第三方索赔等大量场景排除在上限之外，可能导致乙方实际承担接近无限责任。",
                    "suggested_revision": "保留责任上限，将例外限定为数据泄露、知识产权侵权、故意或重大过失，并明确排除间接损失、商誉损失和预期利润损失；系统不可用或输出错误应采用服务信用或封顶违约金处理。",
                    "evidence": "8.1 约定赔偿责任以甲方已实际支付款项为限；8.2 又列出大量不适用责任上限的例外。",
                },
                {
                    "id": "risk_scope_creep",
                    "clause": "1.2 / 1.4 / 12.2",
                    "risk_level": "high",
                    "issue": "甲方可随时调整需求且原则上不增加费用，主观不满意时乙方需持续优化，邮件和会议纪要也可能成为合同组成部分，需求边界过于开放。",
                    "suggested_revision": "建立书面变更单机制，约定影响费用、工期和验收标准的变更需双方确认后执行。",
                    "evidence": "1.2 要求乙方无条件配合需求变更且原则上不增加费用；1.4 要求优化至甲方认可。",
                },
                {
                    "id": "risk_payment_imbalance",
                    "clause": "3.2 / 3.3 / 3.4",
                    "risk_level": "high",
                    "issue": "90% 款项需上线稳定运行 180 日后支付，甲方延迟付款不构成违约且乙方不得暂停服务，现金流和履约风险显著偏高。",
                    "suggested_revision": "改为里程碑付款，约定无争议款项付款期限、逾期利息和合理暂停权。",
                    "evidence": "3.2 仅 10% 预付款；3.3 明确延迟付款不构成违约且乙方不得暂停服务。",
                },
                {
                    "id": "risk_data_privacy",
                    "clause": "4.1 / 4.2 / 4.3 / 4.4",
                    "risk_level": "high",
                    "issue": "合同涉及手机号、地址、购买记录等个人信息，但允许项目结束后继续用于训练，且无需单独签署数据处理协议或取得子处理方书面同意。",
                    "suggested_revision": "补充个人信息处理协议，限定训练用途、留存期限、脱敏要求、子处理方审批和安全事件责任。",
                    "evidence": "4.2 允许乙方项目结束后继续使用数据和日志进行内部模型训练；4.3 排除另行签署数据处理协议。",
                },
                {
                    "id": "risk_acceptance_ambiguity",
                    "clause": "2.2 / 2.4",
                    "risk_level": "medium",
                    "issue": "甲方 3 日内未提出书面异议反而视为交付不合格，且甲方资料延误仍要求乙方按原期限交付，验收机制不客观。",
                    "suggested_revision": "约定明确验收标准、异议清单和视为验收通过机制，并将甲方依赖事项导致的延期顺延。",
                    "evidence": "2.2 将沉默处理为不合格；2.4 将甲方未及时配合导致的延期风险转给乙方。",
                },
                {
                    "id": "risk_ip_ownership",
                    "clause": "5.1 / 5.2 / 5.3 / 5.4",
                    "risk_level": "medium",
                    "issue": "源代码、Prompt、部署脚本和技术文档交付义务与付款条件、背景 IP 和复用权之间存在冲突。",
                    "suggested_revision": "区分定制交付物、背景 IP、开源组件、通用方法和客户使用许可，并将源代码交付与付款节点绑定。",
                    "evidence": "5.2 要求无论是否付款均交付源代码和配置；5.4 又限制乙方复用相似方案。",
                },
                {
                    "id": "risk_sla_unrealistic",
                    "clause": "6.1 / 6.2 / 6.3 / 6.4",
                    "risk_level": "medium",
                    "issue": "99.99% 可用性、10 分钟响应、30 分钟彻底修复、24 个月免费支持和高额违约金组合过重。",
                    "suggested_revision": "改为分级响应、合理排除项、服务信用机制和封顶违约金。",
                    "evidence": "6.3 约定累计超过 1 小时即按合同总价 20% 支付违约金。",
                },
                {
                    "id": "risk_termination_asymmetry",
                    "clause": "9.1 / 9.2 / 9.3 / 9.4",
                    "risk_level": "medium",
                    "issue": "甲方可 3 日便利解除，乙方解除需提前 90 日并取得同意，解除后还需 180 日免费过渡，权利义务明显不对等。",
                    "suggested_revision": "设置对等解除权、合理通知期、已完成工作结算和付费过渡服务。",
                    "evidence": "9.1 与 9.2 的解除条件明显不对称；9.3 要求乙方继续 180 日免费过渡。",
                },
            ],
            {
                "heading": "8.1 / 8.2 保守修订草案",
                "content": "乙方在本合同项下的累计赔偿责任以甲方在索赔发生前十二个月内已实际支付的合同款项为上限。前述责任上限不适用于因乙方故意或重大过失、侵犯第三方知识产权、违反保密义务或经依法认定的数据安全事件造成的直接损失。除法律另有强制规定或双方另有书面约定外，任何一方均不对间接损失、商誉损失、预期利润损失或惩罚性赔偿承担责任。",
                "status": "draft",
                "highlights": ["保留责任上限", "缩窄例外范围", "排除间接与预期利润损失"],
            },
            {
                "content": "用户偏好保守但谈判友好的合同修订风格，尤其关注责任上限、赔偿例外和客户沟通语气。",
                "memory_type": "preference",
                "confidence": 0.82,
            },
        )
    return (
        {
            "high_count": 4,
            "medium_count": 4,
            "low_count": 0,
            "confidence": "0.88",
            "status": "review_ready",
            "summary": "I reviewed the full AI service agreement. Most findings can stay in the full artifact, but clauses 8.1 and 8.2 create a liability cap and indemnity exception conflict that needs direction before revision.",
            "generation_mode": generation_mode,
        },
        [
            {
                "id": "risk_liability_indemnity_conflict",
                "clause": "8.1 / 8.2",
                "risk_level": "high",
                "issue": "Clause 8.1 appears to cap vendor liability, but clause 8.2 excludes broad categories from the cap, including data leakage, IP disputes, regulatory penalties, model output errors, business loss, indirect loss, and third-party claims. The practical result may be near-unlimited liability.",
                "suggested_revision": "Keep the liability cap, limit carve-outs to data breach, IP infringement, willful misconduct, and gross negligence, and exclude indirect loss, goodwill loss, and lost profits. Service outages or output errors should use service credits or capped liquidated damages.",
                "evidence": "8.1 caps liability at amounts actually paid by Customer; 8.2 lists broad exceptions that do not apply to the cap.",
            },
            {
                "id": "risk_scope_creep",
                "clause": "1.2 / 1.4 / 12.2",
                "risk_level": "high",
                "issue": "Customer may change requirements at any time without additional fees, subjective satisfaction controls optimization, and emails or meeting notes can become contract terms.",
                "suggested_revision": "Add a written change order process for scope, fees, schedule, and acceptance criteria.",
                "evidence": "1.2 requires unconditional cooperation with changes; 1.4 requires optimization until Customer recognizes the result.",
            },
            {
                "id": "risk_payment_imbalance",
                "clause": "3.2 / 3.3 / 3.4",
                "risk_level": "high",
                "issue": "Only 10% is prepaid, 90% is delayed until 180 days of stable operation, delayed payment is not breach, and vendor cannot suspend service.",
                "suggested_revision": "Use milestone payments, a clear due date for undisputed amounts, late-payment consequences, and a reasonable suspension right.",
                "evidence": "3.2 requires 90% payment only after 180 days; 3.3 says delayed payment is not breach.",
            },
            {
                "id": "risk_data_privacy",
                "clause": "4.1 / 4.2 / 4.3 / 4.4",
                "risk_level": "high",
                "issue": "The contract covers personal information but allows post-project model training use without a separate data processing agreement or subprocessor consent.",
                "suggested_revision": "Add a data processing agreement covering training limits, retention, de-identification, subprocessor approval, and security incident responsibility.",
                "evidence": "4.2 allows continued use of customer data and logs for internal model training; 4.3 removes a separate data processing agreement.",
            },
            {
                "id": "risk_acceptance_ambiguity",
                "clause": "2.2 / 2.4",
                "risk_level": "medium",
                "issue": "Customer silence after three days means non-acceptance, and Customer delays do not extend the delivery timeline.",
                "suggested_revision": "Add objective acceptance criteria, a defect list process, deemed acceptance, and schedule relief for customer dependencies.",
                "evidence": "2.2 treats silence as failure; 2.4 keeps the original deadline even when Customer dependencies are delayed.",
            },
            {
                "id": "risk_ip_ownership",
                "clause": "5.1 / 5.2 / 5.3 / 5.4",
                "risk_level": "medium",
                "issue": "Source code and prompt delivery obligations conflict with payment conditions, background IP, and reuse rights.",
                "suggested_revision": "Separate custom deliverables, background IP, open-source components, reusable methods, and customer licenses; tie source delivery to payment milestones.",
                "evidence": "5.2 requires source and configuration delivery regardless of payment; 5.4 restricts vendor reuse of similar solutions.",
            },
            {
                "id": "risk_sla_unrealistic",
                "clause": "6.1 / 6.2 / 6.3 / 6.4",
                "risk_level": "medium",
                "issue": "99.99% uptime, 10-minute response, 30-minute complete fix, 24 months of free support, and heavy penalties are unrealistic as a package.",
                "suggested_revision": "Use severity tiers, exclusions, service credits, and capped liquidated damages.",
                "evidence": "6.3 applies a 20% contract-price penalty after one hour of cumulative issues.",
            },
            {
                "id": "risk_termination_asymmetry",
                "clause": "9.1 / 9.2 / 9.3 / 9.4",
                "risk_level": "medium",
                "issue": "Customer can terminate on three days' notice for convenience, while vendor needs 90 days and consent, then must provide 180 days of free transition services.",
                "suggested_revision": "Create mutual termination rights, reasonable notice periods, payment for completed work, and paid transition services.",
                "evidence": "9.1 and 9.2 are asymmetric; 9.3 requires 180 days of free transition support.",
            },
        ],
        {
            "heading": "Conservative revision draft for clauses 8.1 / 8.2",
            "content": "Vendor's aggregate liability under this Agreement is capped at amounts actually paid by Customer in the twelve months before the claim. The cap does not apply to direct losses caused by Vendor's willful misconduct, gross negligence, IP infringement, confidentiality breach, or legally established data security incident. Except where mandatory law requires otherwise, neither party is liable for indirect loss, goodwill loss, lost profits, or punitive damages.",
            "status": "draft",
            "highlights": ["Keeps liability cap", "Narrows carve-outs", "Excludes indirect and lost-profit damages"],
        },
        {
            "content": "User prefers conservative but negotiation-friendly contract revisions, especially for liability caps, indemnity carve-outs, and client-facing tone.",
            "memory_type": "preference",
            "confidence": 0.82,
        },
    )


def _default_contract_review_content(zh: bool, generation_mode: str, fixture_contract: bool = False) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    if fixture_contract:
        return _fixture_contract_review_content(zh, generation_mode)
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
            risk_summary_data, risks, revision_draft, memory_candidate = _default_contract_review_content(zh, generation_mode, _is_problematic_ai_service_contract(task.input_message))
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
                            "target": risks[0]["id"] if risks else "risk_1",
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
