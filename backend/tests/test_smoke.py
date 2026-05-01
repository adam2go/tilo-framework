import os
import tempfile
from pathlib import Path

import pytest

db_path = Path(tempfile.gettempdir()) / "tilo_smoke_test.db"
if db_path.exists():
    db_path.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
os.environ["LLM_ENABLED"] = "false"
os.environ["LLM_PROVIDER"] = "openai"
os.environ["LLM_BASE_URL"] = ""
os.environ["OPENAI_API_KEY"] = ""

from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Confirmation, Memory, Run, Task, TraceStep, UIInteractionEvent  # noqa: E402
from app.services.agent_runtime.run_manager import RunManager  # noqa: E402
from app.services.agent_runtime.prompt_builder import PromptBuilder  # noqa: E402
from app.services.agent_runtime.state_machine import InvalidStateTransition, RunStateMachine  # noqa: E402
from app.services.artifact.generator import ArtifactGenerator  # noqa: E402
from app.services.artifact.spec import ArtifactSpecBuilder  # noqa: E402
from app.services.channels.telegram.adapter import TelegramAdapter  # noqa: E402
from app.services.channels.telegram.types import parse_telegram_callback_data  # noqa: E402
from app.services.artifact.contract_llm import ContractReviewLLMGenerator  # noqa: E402
from app.services.models.client import ModelClient  # noqa: E402
from app.services.models.errors import ModelDisabledError, ModelInvalidJSONError  # noqa: E402
from app.services.demo import classify_followup_deterministic, load_problematic_ai_service_agreement  # noqa: E402
from app.services.apps.loader import get_app_loader  # noqa: E402
from app.services.interaction_policy.schemas import InteractionContext, InteractionDecisionType  # noqa: E402
from app.services.interaction_policy.service import InteractionPolicyService  # noqa: E402
from app.schemas.artifact import ArtifactSpecV1  # noqa: E402
from app.services.trace.recorder import TraceRecorder  # noqa: E402


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_runtime_capabilities_hide_model_secrets() -> None:
    with TestClient(app) as client:
        response = client.get("/api/runtime/capabilities")

    assert response.status_code == 200
    capabilities = response.json()
    assert capabilities["llm_enabled"] is False
    assert capabilities["llm_runtime_mode"] == "deterministic"
    assert capabilities["llm_provider"] == "openai"
    assert "anthropic" in capabilities["llm_supported_providers"]
    assert "deepseek" in capabilities["llm_supported_providers"]
    assert "tencent" in capabilities["llm_supported_providers"]
    assert "custom" in capabilities["llm_supported_providers"]
    assert "openai_api_key" not in capabilities
    assert "api_key" not in capabilities


def test_demo_contract_endpoint_reads_single_source_fixture() -> None:
    fixture = load_problematic_ai_service_agreement()
    with TestClient(app) as client:
        response = client.get("/api/demo/contracts/problematic-ai-service-agreement")

    assert response.status_code == 200
    payload = response.json()
    assert payload["content"] == fixture.content
    assert payload["source_path"] == "examples/contracts/problematic-ai-service-agreement.md"
    assert "**8.1**" in payload["content"]
    assert "**8.2**" in payload["content"]


def test_agent_app_manifest_loader_resolves_contract_review_app() -> None:
    app_manifest = get_app_loader().load_manifest("contract-review-agent")

    assert app_manifest.id == "contract-review-agent"
    assert app_manifest.entry.type == "conversation"
    assert app_manifest.runtime.interaction_policy == "interaction.policy.yaml"
    assert "MiniIssueCard" in app_manifest.surfaces.mini
    assert app_manifest.sample_inputs[0].resolved_path == "examples/contracts/problematic-ai-service-agreement.md"


def test_apps_api_lists_and_reads_contract_review_app() -> None:
    with TestClient(app) as client:
        list_response = client.get("/api/apps")
        detail_response = client.get("/api/apps/contract-review-agent")

    assert list_response.status_code == 200
    assert any(item["id"] == "contract-review-agent" for item in list_response.json())
    assert detail_response.status_code == 200
    assert detail_response.json()["runtime"]["deterministic_fallback"] is True


def test_interaction_policy_evaluates_core_decisions_and_budget() -> None:
    service = InteractionPolicyService()
    policy = service.load_for_app("contract-review-agent")

    high_risk = service.evaluate(
        policy,
        InteractionContext(
            artifact_type="contract_review",
            risk_level="high",
            requires_user_decision=True,
            category="liability",
        ),
    )
    medium_risk = service.evaluate(policy, InteractionContext(artifact_type="contract_review", risk_level="medium"))
    full_review = service.evaluate(policy, InteractionContext(user_action="open_full_review"))
    memory = service.evaluate(policy, InteractionContext(signal="user_preference_detected"))
    unknown = service.evaluate(policy, InteractionContext(artifact_type="contract_review", risk_level="low"))
    budgeted = service.evaluate(
        policy,
        InteractionContext(
            artifact_type="contract_review",
            risk_level="high",
            requires_user_decision=True,
            category="liability",
            mini_surfaces_used=3,
        ),
    )

    assert high_risk.decision == InteractionDecisionType.mini_surface
    assert high_risk.surface == "MiniIssueCard"
    assert medium_risk.decision == InteractionDecisionType.no_ui
    assert full_review.decision == InteractionDecisionType.rich_surface
    assert full_review.surface == "ContractReviewArtifact"
    assert memory.surface == "MiniMemoryCard"
    assert unknown.decision == InteractionDecisionType.no_ui
    assert budgeted.decision == InteractionDecisionType.no_ui
    assert budgeted.reason == "mini_surface_budget_exceeded"


def test_interaction_policy_api_returns_primary_mini_surface() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/apps/contract-review-agent/interaction-policy/evaluate",
            json={
                "artifact_type": "contract_review",
                "risk_level": "high",
                "requires_user_decision": True,
                "category": "liability",
            },
        )

    assert response.status_code == 200
    assert response.json()["decision"] == "mini_surface"
    assert response.json()["surface"] == "MiniIssueCard"


def test_demo_followup_intent_endpoint_uses_deterministic_fallback() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/demo/followup-intent",
            json={"text": "语气不要太强硬，适合发给客户谈判", "locale": "zh"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "revise_tone"
    assert payload["mode"] == "deterministic"


def test_followup_intent_rules_cover_core_demo_intents() -> None:
    assert classify_followup_deterministic("why is clause 8.2 risky?").intent == "focus_clause"
    assert classify_followup_deterministic("draft an email for the customer").intent == "draft_email"
    assert classify_followup_deterministic("以后记住这个偏好").intent == "remember_preference"


def test_model_client_disabled_mode_is_explicit() -> None:
    client = ModelClient(Settings(llm_enabled=False, openai_api_key=""))

    assert client.enabled is False
    with pytest.raises(ModelDisabledError):
        client.chat_text_sync(system="system", user="user")


def test_model_client_resolves_mainstream_provider_presets() -> None:
    deepseek = ModelClient(Settings(llm_enabled=True, llm_provider="deepseek", deepseek_api_key="test-key"))
    anthropic = ModelClient(Settings(llm_enabled=True, llm_provider="anthropic", anthropic_api_key="test-key", default_model="claude-3-5-sonnet-latest"))
    tencent = ModelClient(Settings(llm_enabled=True, llm_provider="tencent", tencent_api_key="test-key", default_model="deepseek-v4-pro"))
    custom = ModelClient(Settings(llm_enabled=True, llm_provider="custom", llm_api_key="test-key", llm_base_url="https://models.example.com/v1"))

    assert deepseek.enabled is True
    assert deepseek.provider_family == "openai_compatible"
    assert deepseek.base_url == "https://api.deepseek.com"
    assert anthropic.enabled is True
    assert anthropic.provider_family == "anthropic"
    assert anthropic.base_url == "https://api.anthropic.com/v1"
    assert tencent.enabled is True
    assert tencent.provider_family == "openai_compatible"
    assert tencent.base_url == "https://tokenhub.tencentmaas.com/v1"
    assert custom.enabled is True
    assert custom.base_url == "https://models.example.com/v1"


def test_contract_review_llm_generator_falls_back_when_disabled() -> None:
    settings = Settings(llm_enabled=False, openai_api_key="")
    task = Task(workspace_id="workspace", title="Contract", input_message="Review payment and liability clauses.")
    result = ContractReviewLLMGenerator(settings).generate(task, [], [])

    assert result.status == "fallback"
    assert result.mode == "deterministic"
    assert result.data is None
    assert result.fallback_reason == "disabled"


def test_contract_review_llm_generator_falls_back_on_invalid_json() -> None:
    class InvalidJSONClient:
        enabled = True

        def chat_json_sync(self, **kwargs):
            raise ModelInvalidJSONError("invalid")

    settings = Settings(llm_enabled=True, openai_api_key="test-key")
    task = Task(workspace_id="workspace", title="Contract", input_message="Review payment and liability clauses.")
    result = ContractReviewLLMGenerator(settings, client=InvalidJSONClient()).generate(task, [], [])

    assert result.status == "fallback"
    assert result.mode == "deterministic"
    assert result.fallback_reason == "ModelInvalidJSONError"


def test_contract_review_llm_generator_prioritizes_liability_conflict_and_caps_full_review_findings() -> None:
    class VerboseClient:
        enabled = True

        def chat_json_sync(self, **kwargs):
            return {
                "risk_summary": {"high_count": 9, "medium_count": 9, "low_count": 9, "summary": "Review summary"},
                "risks": [
                    {"id": "risk_1", "clause": "Low", "risk_level": "low", "issue": "Low issue", "suggested_revision": "Low revision", "evidence": "Low evidence"},
                    {"id": "risk_2", "clause": "High A", "risk_level": "high", "issue": "High issue A", "suggested_revision": "High revision A", "evidence": "High evidence A"},
                    {"id": "risk_3", "clause": "Medium", "risk_level": "medium", "issue": "Medium issue", "suggested_revision": "Medium revision", "evidence": "Medium evidence"},
                    {"id": "risk_4", "clause": "High B", "risk_level": "high", "issue": "High issue B", "suggested_revision": "High revision B", "evidence": "High evidence B"},
                    {"id": "risk_5", "clause": "8.1 / 8.2", "risk_level": "high", "issue": "Liability cap and indemnity carve-outs conflict", "suggested_revision": "Narrow carve-outs", "evidence": "8.1 and 8.2"},
                    {"id": "risk_6", "clause": "Payment", "risk_level": "medium", "issue": "Payment issue", "suggested_revision": "Payment revision", "evidence": "Payment evidence"},
                    {"id": "risk_7", "clause": "SLA", "risk_level": "medium", "issue": "SLA issue", "suggested_revision": "SLA revision", "evidence": "SLA evidence"},
                    {"id": "risk_8", "clause": "IP", "risk_level": "medium", "issue": "IP issue", "suggested_revision": "IP revision", "evidence": "IP evidence"},
                    {"id": "risk_9", "clause": "Extra", "risk_level": "low", "issue": "Extra issue", "suggested_revision": "Extra revision", "evidence": "Extra evidence"},
                ],
                "revision_draft": {"heading": "Draft", "content": "Revision", "highlights": ["one", "two", "three", "four"]},
                "memory_candidate": {"type": "preference", "content": "Remember conservative review", "confidence": 0.8},
            }

    settings = Settings(llm_enabled=True, openai_api_key="test-key")
    task = Task(workspace_id="workspace", title="Contract", input_message="Review payment and liability clauses.")
    result = ContractReviewLLMGenerator(settings, client=VerboseClient()).generate(task, [], [])

    assert result.status == "success"
    assert result.data is not None
    assert result.data.risks[0].clause == "8.1 / 8.2"
    assert len(result.data.risks) == 8
    assert result.data.risk_summary.high_count == 3
    assert result.data.risk_summary.medium_count == 4
    assert result.data.risk_summary.low_count == 1
    assert len(result.data.revision_draft.highlights) == 3


def test_sample_contract_deterministic_artifact_uses_clause_8_primary_issue() -> None:
    task = Task(
        id="task_sample_contract",
        workspace_id="workspace",
        title="Contract",
        input_message="请审查 AI 客服系统定制开发与运维服务合同（问题样例）。\n\n**8.1** 责任上限。\n**8.2** 赔偿例外。",
    )
    run = Run(id="run_sample_contract", task_id="task_sample_contract")
    spec = ArtifactSpecBuilder().build("contract_review", task, run, [], [], generation_mode="deterministic")
    risks = next(block for block in spec["blocks"] if block["id"] == "risk_review")["data"]["risks"]

    assert risks[0]["clause"] == "8.1 / 8.2"
    assert risks[0]["id"] == "risk_liability_indemnity_conflict"
    assert len(risks) >= 8
    assert spec["actions"][0]["payload"]["target"] == "risk_liability_indemnity_conflict"


def test_message_creates_core_loop_records() -> None:
    with TestClient(app) as client:
        bootstrap = client.get("/api/bootstrap").json()
        workspace = bootstrap["workspace"]
        project = bootstrap["projects"][0]
        agent = bootstrap["agents"][0]

        message_response = client.post(
            "/api/messages",
            json={
                "workspace_id": workspace["id"],
                "project_id": project["id"],
                "agent_id": agent["id"],
                "content": "Review this contract and flag risky liability clauses.",
                "attachments": [],
            },
        )
        assert message_response.status_code == 200
        message = message_response.json()

        artifacts = client.get(
            "/api/artifacts",
            params={"workspace_id": workspace["id"], "task_id": message["task_id"]},
        ).json()
        trace = client.get(f"/api/runs/{message['run_id']}/trace").json()
        recall_events = client.get(
            "/api/memories/events/recall",
            params={"workspace_id": workspace["id"], "run_id": message["run_id"]},
        ).json()
        write_events = client.get("/api/memories/events/write", params={"workspace_id": workspace["id"]}).json()
        tool_invocations = client.get(
            "/api/tools/invocations",
            params={"workspace_id": workspace["id"], "run_id": message["run_id"]},
        ).json()
        confirmations = client.get(
            "/api/confirmations",
            params={"workspace_id": workspace["id"], "status": "pending"},
        ).json()
        memories = client.get("/api/memories", params={"workspace_id": workspace["id"]}).json()
        metrics = client.get(f"/api/runs/{message['run_id']}/metrics").json()
        feedback_response = client.post(
            "/api/feedback",
            json={
                "workspace_id": workspace["id"],
                "project_id": project["id"],
                "run_id": message["run_id"],
                "artifact_id": artifacts[0]["id"],
                "rating": 5,
                "feedback_type": "useful",
                "feedback_text": "Useful result. Save this as a skill after review.",
            },
        )
        candidates = client.get("/api/skills/candidates", params={"workspace_id": workspace["id"]}).json()
        approved_candidate = client.post(f"/api/skills/candidates/{candidates[0]['id']}/approve").json()
        promoted_skill = client.post(f"/api/skills/candidates/{candidates[0]['id']}/promote").json()

    assert message["status"] == "completed"
    assert artifacts and artifacts[0]["schema_json"]["version"] == "artifact_spec.v1"
    assert artifacts[0]["schema_json"]["artifact_type"] == "contract_review"
    assert any(block["type"] == "risk_review_panel" for block in artifacts[0]["schema_json"]["blocks"])
    assert any(block.get("actions") for block in artifacts[0]["schema_json"]["blocks"])
    assert artifacts[0]["schema_json"]["actions"]
    assert artifacts[0]["schema_json"]["actions"][0]["confirmation_required"] is True
    assert artifacts[0]["schema_json"]["actions"][0]["confirmation_id"]
    assert any(step["step_type"] == "recall_memory" for step in trace)
    assert any(step["step_type"] == "generate_artifact" for step in trace)
    assert recall_events and recall_events[0]["strategy"] == "hybrid_v0.2"
    assert any(event["event_type"] == "candidate_created" for event in write_events)
    assert tool_invocations and tool_invocations[0]["status"] == "completed"
    assert tool_invocations[0]["output_json"]["mock"] is True
    assert confirmations
    assert any(memory["status"] == "candidate" and memory["is_confirmed"] is False for memory in memories)
    assert metrics["success"] is True
    assert metrics["artifact_count"] == 1
    assert metrics["confirmation_count"] >= 1
    assert metrics["memory_candidate_count"] == 1
    assert feedback_response.status_code == 200
    assert candidates and candidates[0]["status"] == "pending_review"
    assert candidates[0]["artifact_template_json"]["run_id"] is None
    assert "confirmation_id" not in candidates[0]["artifact_template_json"]["actions"][0]
    assert approved_candidate["status"] == "approved"
    assert promoted_skill["name"] == approved_candidate["name"]


def test_chinese_contract_review_uses_chinese_artifact_labels() -> None:
    with TestClient(app) as client:
        bootstrap = client.get("/api/bootstrap").json()
        workspace = bootstrap["workspace"]
        project = bootstrap["projects"][0]
        agent = bootstrap["agents"][0]

        message_response = client.post(
            "/api/messages",
            json={
                "workspace_id": workspace["id"],
                "project_id": project["id"],
                "agent_id": agent["id"],
                "content": "请用简体中文审查这份合同中的付款、责任限制和终止条款风险。",
                "attachments": [],
            },
        )
        message = message_response.json()
        artifacts = client.get(
            "/api/artifacts",
            params={"workspace_id": workspace["id"], "task_id": message["task_id"]},
        ).json()

    assert message_response.status_code == 200
    assert artifacts[0]["title"] == "合同审查"
    assert artifacts[0]["schema_json"]["title"] == "合同审查"
    assert artifacts[0]["schema_json"]["blocks"][0]["title"] == "风险摘要"
    assert artifacts[0]["schema_json"]["actions"][0]["label"] == "批准责任条款修订"


def test_ui_interaction_event_api_persists_sanitized_observations() -> None:
    with TestClient(app) as client:
        bootstrap = client.get("/api/bootstrap").json()
        workspace = bootstrap["workspace"]
        project = bootstrap["projects"][0]

        event_response = client.post(
            "/api/interactions",
            json={
                "workspace_id": workspace["id"],
                "project_id": project["id"],
                "artifact_id": "artifact-1",
                "block_id": "approval",
                "action_id": "approve",
                "run_id": "run-1",
                "event_type": "artifact.action.approved",
                "payload": {"token": "secret-value", "choice": "approve"},
            },
        )
        events = client.get(
            "/api/interactions",
            params={"workspace_id": workspace["id"], "artifact_id": "artifact-1", "run_id": "run-1"},
        ).json()

    assert event_response.status_code == 200
    event = event_response.json()
    assert event["event_type"] == "artifact.action.approved"
    assert event["payload_json"]["token"] == "[REDACTED]"
    assert events and events[0]["block_id"] == "approval"


def test_prompt_builder_includes_recent_ui_observations_without_turning_them_into_memory() -> None:
    event = UIInteractionEvent(
        workspace_id="workspace",
        event_type="artifact.action.approved",
        artifact_id="artifact-1",
        run_id="run-1",
        payload_json={"choice": "approve"},
    )
    task = Task(workspace_id="workspace", title="Follow-up", input_message="Continue from the last approval.")

    prompt = PromptBuilder().build(task, None, [], [], [], [event])

    assert prompt["recent_ui_observations"][0]["event_type"] == "artifact.action.approved"
    assert prompt["recent_ui_observations"][0]["payload"] == {"choice": "approve"}
    assert prompt["memories"] == []


def test_telegram_normalizes_text_message_and_callback_query() -> None:
    adapter = TelegramAdapter()
    message_event = adapter.receive(
        {
            "update_id": 1,
            "message": {
                "message_id": 42,
                "from": {"id": 1001},
                "chat": {"id": 2002},
                "text": "Review this contract",
            },
        }
    )
    callback_event = adapter.receive(
        {
            "update_id": 2,
            "callback_query": {
                "id": "callback-1",
                "from": {"id": 1001},
                "message": {"message_id": 43, "chat": {"id": 2002}, "text": "Approval needed"},
                "data": "tilo:approve_confirmation:abc123",
            },
        }
    )
    parsed = parse_telegram_callback_data("tilo:confirm_memory:def456")

    assert message_event.event_type == "channel.message.received"
    assert message_event.external_user_id == "1001"
    assert message_event.external_chat_id == "2002"
    assert message_event.text == "Review this contract"
    assert callback_event.event_type == "channel.callback.clicked"
    assert callback_event.callback_data["action"] == "approve_confirmation"
    assert callback_event.callback_data["target_id"] == "abc123"
    assert parsed and parsed.action == "confirm_memory"


def test_telegram_webhook_text_message_creates_task_run_and_artifact_link() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/channels/telegram/webhook",
            json={
                "update_id": 10,
                "message": {
                    "message_id": 100,
                    "from": {"id": 9001},
                    "chat": {"id": 8001},
                    "text": "Review this contract and flag risky termination clauses.",
                },
            },
        )
        body = response.json()

    assert response.status_code == 200
    assert body["status"] == "ok"
    assert body["task_id"]
    assert body["run_id"]
    assert body["artifact_id"]
    assert body["telegram_response"]["chat_id"] == "8001"
    assert body["telegram_response"]["reply_markup"]["inline_keyboard"][0][0]["url"].endswith(
        f"/artifacts/{body['artifact_id']}?channel=telegram&chat_id=8001"
    )


def test_telegram_callback_approves_confirmation_and_records_interaction() -> None:
    with TestClient(app) as client:
        bootstrap = client.get("/api/bootstrap").json()
        workspace = bootstrap["workspace"]
        with SessionLocal() as db:
            confirmation = Confirmation(
                workspace_id=workspace["id"],
                type="approval",
                title="Approve revision",
                description="Approve conservative revision.",
                payload_json={},
            )
            db.add(confirmation)
            db.commit()
            db.refresh(confirmation)
            confirmation_id = confirmation.id

        response = client.post(
            "/api/channels/telegram/webhook",
            json={
                "update_id": 11,
                "callback_query": {
                    "id": "callback-2",
                    "from": {"id": 9001},
                    "message": {"message_id": 101, "chat": {"id": 8001}, "text": "Approval needed"},
                    "data": f"tilo:approve_confirmation:{confirmation_id[:32]}",
                },
            },
        )
        body = response.json()

        with SessionLocal() as db:
            updated = db.get(Confirmation, confirmation_id)
            interaction = db.query(UIInteractionEvent).filter(UIInteractionEvent.workspace_id == workspace["id"]).order_by(UIInteractionEvent.created_at.desc()).first()

    assert response.status_code == 200
    assert body["confirmation_id"] == confirmation_id
    assert updated.status == "approved"
    assert updated.decision_json["decision"]["source"] == "telegram"
    assert interaction.event_type == "channel.telegram.approve_confirmation"
    assert interaction.payload_json["external_chat_id"] == "8001"


def test_telegram_callback_confirms_memory_candidate() -> None:
    with TestClient(app) as client:
        bootstrap = client.get("/api/bootstrap").json()
        workspace = bootstrap["workspace"]
        with SessionLocal() as db:
            memory = Memory(
                workspace_id=workspace["id"],
                type="preference",
                content="User prefers conservative contract review.",
                source_type="manual",
                status="candidate",
                is_confirmed=False,
            )
            db.add(memory)
            db.commit()
            db.refresh(memory)
            memory_id = memory.id

        response = client.post(
            "/api/channels/telegram/webhook",
            json={
                "update_id": 12,
                "callback_query": {
                    "id": "callback-3",
                    "from": {"id": 9001},
                    "message": {"message_id": 102, "chat": {"id": 8001}, "text": "Remember this?"},
                    "data": f"tilo:confirm_memory:{memory_id[:32]}",
                },
            },
        )

        with SessionLocal() as db:
            updated = db.get(Memory, memory_id)

    assert response.status_code == 200
    assert response.json()["memory_id"] == memory_id
    assert updated.status == "confirmed"
    assert updated.is_confirmed is True


def test_artifact_schema_accepts_roam_actions_and_state_binding() -> None:
    spec = ArtifactSpecV1.model_validate(
        {
            "artifact_type": "demo",
            "title": "ROAM Demo",
            "blocks": [
                {
                    "id": "approval",
                    "type": "approval_card",
                    "data": {"title": "Approve"},
                    "state_binding": {"entity_type": "run", "entity_id": "run-1"},
                    "actions": [
                        {
                            "id": "approve",
                            "label": "Approve",
                            "action_type": "approve",
                            "confirmation_required": True,
                            "state_binding": {"entity_type": "confirmation", "entity_id": "confirmation-1"},
                        }
                    ],
                }
            ],
        }
    )

    assert spec.blocks[0].type == "approval_card"
    assert spec.blocks[0].actions[0].action_type == "approve"
    assert spec.blocks[0].state_binding.entity_type == "run"


def test_state_machine_rejects_invalid_transitions() -> None:
    task = Task(workspace_id="workspace", title="Task", input_message="Input", status="created")
    run = Run(task_id="task", status="queued")
    state_machine = RunStateMachine()

    state_machine.transition(task, run, "running")
    state_machine.transition(task, run, "completed")

    try:
        state_machine.transition(task, run, "running")
    except InvalidStateTransition as exc:
        assert "completed -> running" in str(exc)
    else:
        raise AssertionError("Completed run should not transition back to running")


def test_trace_sanitizes_sensitive_payloads() -> None:
    with TestClient(app):
        with SessionLocal() as db:
            task = Task(workspace_id="workspace", title="Trace safety", input_message="Input")
            db.add(task)
            db.flush()
            run = Run(task_id=task.id)
            db.add(run)
            db.commit()
            db.refresh(run)

            step = TraceRecorder(db).record(
                run.id,
                "trace_safety",
                "Trace safety",
                "Sanitize sensitive input.",
                input_json={"api_key": "secret-value", "query": "safe"},
                output_json={"text": "token=secret-value", "items": list(range(25))},
            )

            assert step.input_json == {"api_key": "[REDACTED]", "query": "safe"}
            assert step.output_json["text"] == "[REDACTED]"
            assert step.output_json["items"][-1] == {"truncated": 5}


def test_run_manager_marks_failed_runs(monkeypatch) -> None:
    def fail_generate(*args, **kwargs):
        raise RuntimeError("token=super-secret")

    monkeypatch.setattr(ArtifactGenerator, "generate", fail_generate)

    with TestClient(app):
        with SessionLocal() as db:
            task = Task(workspace_id="workspace", title="Failure path", input_message="contract failure path")
            db.add(task)
            db.flush()
            run = Run(task_id=task.id)
            db.add(run)
            db.commit()
            db.refresh(task)
            db.refresh(run)

            result = RunManager(db).execute(task, run)
            failed_step = db.query(TraceStep).filter(TraceStep.run_id == run.id, TraceStep.status == "failed").one()

            assert result == {"artifacts": [], "confirmations": [], "memory_candidates": []}
            assert task.status == "failed"
            assert run.status == "failed"
            assert run.error_message == "[REDACTED]"
            assert failed_step.step_type == "runtime_error"
            assert failed_step.output_json["error"] == "[REDACTED]"


def test_high_risk_tool_invocation_requires_confirmation() -> None:
    with TestClient(app) as client:
        bootstrap = client.get("/api/bootstrap").json()
        workspace = bootstrap["workspace"]

        tool = client.post(
            "/api/tools",
            json={
                "workspace_id": workspace["id"],
                "name": "Mock Sender",
                "type": "mock_browser",
                "description": "High-risk mock external sender.",
                "config_json": {},
                "permission_level": "high",
            },
        ).json()
        invocation_response = client.post(
            f"/api/tools/{tool['id']}/invoke",
            json={"input": {"message": "send update", "token": "super-secret"}},
        ).json()
        invocation_id = invocation_response["tool_invocation_id"]
        invocation = client.get(f"/api/tools/invocations/{invocation_id}").json()
        run = client.get(f"/api/runs/{invocation_response['run_id']}").json()
        confirmations = client.get(
            "/api/confirmations",
            params={"workspace_id": workspace["id"], "status": "pending"},
        ).json()

    assert invocation_response["output"]["status"] == "confirmation_required"
    assert invocation["status"] == "pending_confirmation"
    assert invocation["permission_level"] == "high"
    assert invocation["input_json"]["token"] == "[redacted]"
    assert invocation["confirmation_id"] == invocation_response["output"]["confirmation_id"]
    assert run["status"] == "waiting_for_confirmation"
    assert any(item["payload_json"].get("tool_invocation_id") == invocation_id for item in confirmations)
