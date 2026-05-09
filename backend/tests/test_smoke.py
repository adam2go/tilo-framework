import os
import json
import subprocess
import sys
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
from app.models import Artifact, Confirmation, ContextReflection, ConversationSession, ConversationTurn, Memory, Run, Task, Tool, TraceStep, UIInteractionEvent  # noqa: E402
from app.services.agent_context import AgentContextBuilder  # noqa: E402
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
from app.services.demo import load_problematic_ai_service_agreement  # noqa: E402
from app.services.apps.loader import AgentAppLoader, get_app_loader  # noqa: E402
from app.services.conversations.constants import ConversationChannel, ConversationTurnType  # noqa: E402
from app.services.conversations.service import ConversationService  # noqa: E402
from app.services.context_reflection import ContextReflectionService  # noqa: E402
from app.services.interaction_policy.schemas import InteractionContext, InteractionDecisionType  # noqa: E402
from app.services.interaction_policy.service import InteractionPolicyService  # noqa: E402
from app.schemas import RichSurfaceLink  # noqa: E402
from app.schemas.artifact import ArtifactSpecV1  # noqa: E402
from app.services.surfaces.constants import RichSurfaceSource, RichSurfaceTargetType  # noqa: E402
from app.services.surfaces.rich_links import create_rich_surface_link  # noqa: E402
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


def test_sales_followup_app_manifest_and_policy_are_loadable() -> None:
    app_manifest = get_app_loader().load_manifest("sales-followup-agent")
    decision = InteractionPolicyService().evaluate_for_app(
        "sales-followup-agent",
        InteractionContext(signal="followup_tone_needed"),
    )
    rich = InteractionPolicyService().evaluate_for_app(
        "sales-followup-agent",
        InteractionContext(user_action="open_full_review"),
    )
    fixture_path = Path(__file__).resolve().parents[2] / app_manifest.sample_inputs[0].resolved_path
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    assert app_manifest.id == "sales-followup-agent"
    assert app_manifest.entry.type == "conversation"
    assert app_manifest.sample_inputs[0].resolved_path == "examples/fixtures/sales-followup-sample.json"
    assert fixture["lead"]["account"] == "Acme Procurement Team"
    assert decision.decision == InteractionDecisionType.mini_surface
    assert decision.surface == "MiniChoiceCard"
    assert rich.decision == InteractionDecisionType.rich_surface
    assert rich.surface == "FollowupDraftArtifact"


def test_validate_app_script_accepts_existing_example_apps() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    for app_path in ("examples/apps/contract-review-agent", "examples/apps/sales-followup-agent"):
        result = subprocess.run(
            [sys.executable, "scripts/validate_app.py", app_path],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "app validation passed" in result.stdout


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
    revision = service.evaluate(policy, InteractionContext(user_action="approve_revision"))
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
    assert high_risk.rule_id == "high-risk-liability-needs-confirmation"
    assert medium_risk.decision == InteractionDecisionType.no_ui
    assert full_review.decision == InteractionDecisionType.rich_surface
    assert full_review.surface == "ContractReviewArtifact"
    assert memory.surface == "MiniMemoryCard"
    assert revision.surface == "MiniRevisionPreview"
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
    assert response.json()["rule_id"] == "high-risk-liability-needs-confirmation"


def test_policy_surface_validation_rejects_undeclared_surface(tmp_path: Path) -> None:
    app_dir = tmp_path / "bad-agent"
    app_dir.mkdir()
    (app_dir / "app.yaml").write_text(
        """
id: bad-agent
version: "0.1"
name: Bad Agent
description: Bad manifest
entry:
  type: conversation
  default_prompt: Hello
runtime:
  model: default
  deterministic_fallback: true
  memory: enabled
  interaction_policy: interaction.policy.yaml
surfaces:
  mini:
    - MiniIssueCard
  rich: []
sample_inputs: []
tools: []
channels:
  - web
""",
        encoding="utf-8",
    )
    (app_dir / "interaction.policy.yaml").write_text(
        """
id: bad-policy
version: "0.1"
rules:
  - id: missing-surface
    when:
      signal: test
    decision: mini_surface
    surface: MiniMemoryCard
    reason: missing
""",
        encoding="utf-8",
    )

    loader = AgentAppLoader(tmp_path)
    service = InteractionPolicyService()
    policy = service.load_file(loader.load_policy_path("bad-agent"))

    with pytest.raises(ValueError, match="undeclared mini surface"):
        service.validate_for_app(loader.load_manifest("bad-agent"), policy)


def test_policy_surface_validation_rejects_undeclared_rich_surface(tmp_path: Path) -> None:
    app_dir = tmp_path / "bad-rich-agent"
    app_dir.mkdir()
    (app_dir / "app.yaml").write_text(
        """
id: bad-rich-agent
version: "0.1"
name: Bad Rich Agent
description: Bad manifest
entry:
  type: conversation
  default_prompt: Hello
runtime:
  model: default
  deterministic_fallback: true
  memory: enabled
  interaction_policy: interaction.policy.yaml
surfaces:
  mini: []
  rich:
    - DeclaredArtifact
sample_inputs: []
tools: []
channels:
  - web
""",
        encoding="utf-8",
    )
    (app_dir / "interaction.policy.yaml").write_text(
        """
id: bad-rich-policy
version: "0.1"
rules:
  - id: missing-rich-surface
    when:
      user_action: open_full_review
    decision: rich_surface
    surface: MissingArtifact
    reason: missing
""",
        encoding="utf-8",
    )

    loader = AgentAppLoader(tmp_path)
    service = InteractionPolicyService()
    policy = service.load_file(loader.load_policy_path("bad-rich-agent"))

    with pytest.raises(ValueError, match="undeclared rich surface"):
        service.validate_for_app(loader.load_manifest("bad-rich-agent"), policy)


def test_manifest_loader_restricts_sample_paths(tmp_path: Path) -> None:
    app_dir = tmp_path / "unsafe-sample-agent"
    app_dir.mkdir()
    (app_dir / "app.yaml").write_text(
        """
id: unsafe-sample-agent
version: "0.1"
name: Unsafe Agent
description: Unsafe manifest
entry:
  type: conversation
  default_prompt: Hello
runtime:
  model: default
  deterministic_fallback: true
  memory: enabled
  interaction_policy: interaction.policy.yaml
surfaces:
  mini: []
  rich: []
sample_inputs:
  - type: fixture
    name: unsafe
    path: ../../../outside.txt
tools: []
channels:
  - web
""",
        encoding="utf-8",
    )
    (app_dir / "interaction.policy.yaml").write_text("id: safe\nversion: '0.1'\nrules: []\n", encoding="utf-8")

    loader = AgentAppLoader(tmp_path)

    with pytest.raises(ValueError, match="Sample input"):
        loader.load_manifest("unsafe-sample-agent")


def test_manifest_loader_restricts_policy_paths(tmp_path: Path) -> None:
    app_dir = tmp_path / "unsafe-policy-agent"
    app_dir.mkdir()
    (app_dir / "app.yaml").write_text(
        """
id: unsafe-policy-agent
version: "0.1"
name: Unsafe Agent
description: Unsafe manifest
entry:
  type: conversation
  default_prompt: Hello
runtime:
  model: default
  deterministic_fallback: true
  memory: enabled
  interaction_policy: ../outside.policy.yaml
surfaces:
  mini: []
  rich: []
sample_inputs: []
tools: []
channels:
  - web
""",
        encoding="utf-8",
    )
    (tmp_path / "outside.policy.yaml").write_text("id: outside\nversion: '0.1'\nrules: []\n", encoding="utf-8")

    loader = AgentAppLoader(tmp_path)

    with pytest.raises(ValueError, match="outside app directory"):
        loader.load_policy_path("unsafe-policy-agent")


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


def test_interaction_with_session_appends_observation_and_context_reflection_candidate() -> None:
    workspace_id = "interaction-reflection-workspace"
    with TestClient(app) as client:
        session = client.post(
            "/api/conversations",
            json={"app_id": "contract-review-agent", "workspace_id": workspace_id, "channel": "web"},
        ).json()
        response = client.post(
            "/api/interactions",
            json={
                "workspace_id": workspace_id,
                "session_id": session["id"],
                "artifact_id": "artifact-reflection",
                "run_id": "run-reflection",
                "event_type": "demo.approve_revision",
                "payload": {"action": "approve_revision", "clauses": "8.1 / 8.2"},
            },
        )
        turns = client.get(f"/api/conversations/{session['id']}/turns").json()

    assert response.status_code == 200
    assert any(turn["turn_type"] == "observation" and turn["interaction_id"] == response.json()["id"] for turn in turns)
    assert any(turn["turn_type"] == "memory_candidate" for turn in turns)
    with SessionLocal() as db:
        reflection = db.query(ContextReflection).filter(ContextReflection.session_id == session["id"]).one()
        memory = db.query(Memory).filter(Memory.workspace_id == workspace_id, Memory.source_type == "context_reflection").one()
        assert reflection.orid_json["objective"]["facts"]
        assert reflection.orid_json["reflective"]["signals"]
        assert reflection.orid_json["interpretive"]["insights"]
        assert reflection.orid_json["decisional"][0]["action"] == "propose_memory"
        assert memory.status == "candidate"
        assert memory.is_confirmed is False
        assert memory.structured_payload["source"] == "context_reflection"
        assert memory.structured_payload["why"]
        assert memory.structured_payload["orid_evidence"]["objective"]


def test_context_reflection_orid_tone_candidate_and_memory_suppression() -> None:
    with TestClient(app):
        with SessionLocal() as db:
            conversation = ConversationService(db)
            tone_session = conversation.create_or_get_session(
                app_id="contract-review-agent",
                workspace_id="orid-tone-workspace",
                channel=ConversationChannel.web,
            )
            conversation.append_user_message(tone_session.id, "语气不要太强硬，适合发给客户谈判")
            tone_event = UIInteractionEvent(
                workspace_id="orid-tone-workspace",
                event_type="demo.text_followup",
                payload_json={"content": "语气不要太强硬，适合发给客户谈判"},
            )
            db.add(tone_event)
            db.commit()
            db.refresh(tone_event)
            reflection = ContextReflectionService(db).reflect_and_persist(session_id=tone_session.id, trigger_event_id=tone_event.id)

            skip_session = conversation.create_or_get_session(
                app_id="contract-review-agent",
                workspace_id="orid-skip-workspace",
                channel=ConversationChannel.web,
            )
            skip_event = UIInteractionEvent(
                workspace_id="orid-skip-workspace",
                event_type="demo.skip_memory",
                payload_json={"action": "not_now"},
            )
            db.add(skip_event)
            db.commit()
            db.refresh(skip_event)
            skip_reflection = ContextReflectionService(db).reflect_and_persist(session_id=skip_session.id, trigger_event_id=skip_event.id)
            tone_memory = db.query(Memory).filter(Memory.workspace_id == "orid-tone-workspace", Memory.source_type == "context_reflection").one()
            skip_memory_count = db.query(Memory).filter(Memory.workspace_id == "orid-skip-workspace", Memory.source_type == "context_reflection").count()
            reflection_orid = reflection.orid_json
            skip_actions = skip_reflection.proposed_actions_json
            tone_memory_status = tone_memory.status
            tone_memory_confirmed = tone_memory.is_confirmed
            tone_memory_payload = tone_memory.structured_payload

    assert reflection_orid["objective"]["facts"][0].startswith("UI event recorded:")
    assert any("User message:" in fact for fact in reflection_orid["objective"]["facts"])
    assert "likely" not in " ".join(reflection_orid["objective"]["facts"]).lower()
    assert tone_memory_status == "candidate"
    assert tone_memory_confirmed is False
    assert tone_memory_payload["orid_evidence"]["reflective"]
    assert skip_actions[0]["action"] == "none"
    assert skip_memory_count == 0


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
    assert prompt["conversation_context"]["recent_observations"][0]["event_type"] == "artifact.action.approved"
    assert prompt["memories"] == []
    assert prompt["recent_conversation_turns"] == []


def test_prompt_builder_includes_and_caps_recent_conversation_turns() -> None:
    task = Task(workspace_id="workspace", title="Follow-up", input_message="Continue.")
    long_content = "x" * 700
    turns = [{"turn_type": "user_message", "role": "user", "content": f"turn {index} {long_content}"} for index in range(14)]

    prompt = PromptBuilder().build(task, None, [], [], [], [], turns)

    assert len(prompt["conversation_context"]["recent_turns"]) == 12
    assert prompt["conversation_context"]["recent_turns"][0]["content"].startswith("turn 2")
    assert len(prompt["conversation_context"]["recent_turns"][0]["content"]) < 560
    assert prompt["memories"] == []


def test_run_manager_passes_session_turns_into_prompt_and_trace(monkeypatch) -> None:
    captured: dict[str, list[dict]] = {}
    original_build = PromptBuilder.build

    def capture_build(self, task, agent, memories, skills, tools, recent_ui_observations=None, recent_conversation_turns=None):
        captured["turns"] = recent_conversation_turns or []
        return original_build(self, task, agent, memories, skills, tools, recent_ui_observations, recent_conversation_turns)

    monkeypatch.setattr(PromptBuilder, "build", capture_build)

    with TestClient(app):
        with SessionLocal() as db:
            session = ConversationService(db).create_or_get_session(
                app_id="contract-review-agent",
                workspace_id="run-manager-session-workspace",
                channel=ConversationChannel.web,
            )
            ConversationService(db).append_user_message(session.id, "Continue with the customer-friendly revision.")
            task = Task(workspace_id="run-manager-session-workspace", title="Session bridge", input_message="Continue the review.")
            db.add(task)
            db.flush()
            run = Run(task_id=task.id, session_id=session.id)
            db.add(run)
            db.commit()
            db.refresh(task)
            db.refresh(run)

            RunManager(db).execute(task, run)
            prompt_step = db.query(TraceStep).filter(TraceStep.run_id == run.id, TraceStep.step_type == "build_prompt").one()

    assert captured["turns"][0]["content"] == "Continue with the customer-friendly revision."
    assert prompt_step.output_json["recent_conversation_turn_count"] == 1
    assert prompt_step.output_json["recent_ui_observation_count"] == 0


def test_conversation_session_and_turn_apis_and_lookup() -> None:
    with TestClient(app) as client:
        workspace_id = client.get("/api/bootstrap").json()["workspace"]["id"]
        create = client.post(
            "/api/conversations",
            json={"app_id": "contract-review-agent", "workspace_id": workspace_id, "channel": "telegram", "external_thread_id": "chat-01"},
        )
        create_again = client.post(
            "/api/conversations",
            json={"app_id": "contract-review-agent", "workspace_id": workspace_id, "channel": "telegram", "external_thread_id": "chat-01"},
        )
        session_id = create.json()["id"]
        turn = client.post(f"/api/conversations/{session_id}/turns", json={"turn_type": "user_message", "role": "user", "content": "hello"})
        turns = client.get(f"/api/conversations/{session_id}/turns")

    assert create.status_code == 200
    assert create_again.json()["id"] == session_id
    assert turn.status_code == 200
    assert turns.json()[0]["content"] == "hello"


def test_conversation_service_create_lookup_append_and_observation_linkage() -> None:
    with TestClient(app):
        with SessionLocal() as db:
            service = ConversationService(db)
            session = service.create_or_get_session(
                app_id="contract-review-agent",
                workspace_id="conversation-service-workspace",
                channel=ConversationChannel.telegram,
                external_thread_id="thread-42",
                external_user_id="user-42",
            )
            same = service.create_or_get_session(
                app_id="contract-review-agent",
                workspace_id="conversation-service-workspace",
                channel=ConversationChannel.telegram,
                external_thread_id="thread-42",
            )
            event = UIInteractionEvent(
                workspace_id="conversation-service-workspace",
                event_type="artifact.action.approved",
                artifact_id="artifact-42",
                action_id="approve",
                run_id="run-42",
                payload_json={"token": "secret-value", "choice": "approve"},
            )
            db.add(event)
            db.commit()
            db.refresh(event)

            service.append_user_message(session.id, "hello")
            service.append_agent_message(session.id, "hi")
            service.append_attachment(session.id, content="lead.json", payload={"kind": "fixture"})
            service.append_mini_surface(session.id, surface_type="MiniChoiceCard", payload={"question": "Tone?"})
            observation = service.append_observation_for_interaction(session.id, event)
            turns = service.list_turns(session.id)
            session_id = session.id
            same_id = same.id
            found_id = service.find_by_external_thread(
                channel=ConversationChannel.telegram,
                external_thread_id="thread-42",
                workspace_id="conversation-service-workspace",
            ).id
            turn_types = [turn.turn_type for turn in turns]
            observation_interaction_id = observation.interaction_id
            observation_payload = observation.observation_payload_json
            event_id = event.id

    assert same_id == session_id
    assert found_id == session_id
    assert turn_types == ["user_message", "agent_message", "attachment", "mini_surface", "observation"]
    assert observation_interaction_id == event_id
    assert observation_payload["payload"]["token"] == "[REDACTED]"


def test_conversation_api_rejects_invalid_turn_type() -> None:
    with TestClient(app) as client:
        workspace_id = client.get("/api/bootstrap").json()["workspace"]["id"]
        session = client.post("/api/conversations", json={"app_id": "contract-review-agent", "workspace_id": workspace_id}).json()
        response = client.post(f"/api/conversations/{session['id']}/turns", json={"turn_type": "unknown_turn", "content": "bad"})

    assert response.status_code == 422


def test_conversation_message_endpoint_creates_session_bound_run_and_turns() -> None:
    with TestClient(app) as client:
        bootstrap = client.get("/api/bootstrap").json()
        workspace = bootstrap["workspace"]
        project = bootstrap["projects"][0]
        agent = bootstrap["agents"][0]
        session = client.post(
            "/api/conversations",
            json={
                "app_id": "contract-review-agent",
                "workspace_id": workspace["id"],
                "project_id": project["id"],
                "agent_id": agent["id"],
                "channel": "web",
            },
        ).json()
        response = client.post(
            f"/api/conversations/{session['id']}/messages",
            json={"content": "Review this contract in the current conversation.", "attachments": [{"name": "contract.md", "type": "fixture"}]},
        )
        message = response.json()
        run = client.get(f"/api/runs/{message['run_id']}").json()
        turns = client.get(f"/api/conversations/{session['id']}/turns").json()
        trace = client.get(f"/api/runs/{message['run_id']}/trace").json()

    assert response.status_code == 200
    assert message["session_id"] == session["id"]
    assert run["session_id"] == session["id"]
    assert any(turn["turn_type"] == "user_message" for turn in turns)
    assert any(turn["turn_type"] == "attachment" for turn in turns)
    assert any(turn["turn_type"] == "agent_message" for turn in turns)
    assert any(turn["turn_type"] == "rich_surface_link" for turn in turns)
    prompt_step = next(step for step in trace if step["step_type"] == "build_prompt")
    assert prompt_step["output_json"]["recent_conversation_turn_count"] >= 2
    assert prompt_step["output_json"]["confirmed_memory_count"] >= 0


def test_roam_contract_review_message_action_observation_memory_contract() -> None:
    workspace_id = "roam-contract-workspace"
    fixture = load_problematic_ai_service_agreement()

    with TestClient(app) as client:
        session = client.post(
            "/api/conversations",
            json={"app_id": "contract-review-agent", "workspace_id": workspace_id, "channel": "web"},
        ).json()
        message = client.post(
            f"/api/conversations/{session['id']}/messages",
            json={
                "content": f"Review this contract and propose a conservative liability revision.\n\n{fixture.content}",
                "attachments": [{"name": fixture.file_name, "type": "sample_contract", "source_path": fixture.source_path}],
            },
        ).json()
        artifacts = client.get("/api/artifacts", params={"workspace_id": workspace_id, "task_id": message["task_id"]}).json()
        artifact = artifacts[0]
        action = next(item for item in artifact["schema_json"]["actions"] if item["id"] == "approve_liability_revision")
        action_response = client.post(
            f"/api/artifacts/{artifact['id']}/actions/{action['id']}",
            json={
                "session_id": session["id"],
                "run_id": message["run_id"],
                "source": "web",
                "payload": {"choice": "approve_revision"},
            },
        )
        action_result = action_response.json()
        turns = client.get(f"/api/conversations/{session['id']}/turns").json()
        memories = client.get("/api/memories", params={"workspace_id": workspace_id, "status": "candidate"}).json()
        reflection_memory = next(memory for memory in memories if memory["source_type"] == "context_reflection")
        confirmed_memory = client.post(f"/api/memories/{reflection_memory['id']}/confirm").json()

    assert message["status"] == "completed"
    assert artifact["schema_json"]["version"] == "artifact_spec.v1"
    assert artifact["schema_json"]["artifact_type"] == "contract_review"
    assert action["confirmation_required"] is True
    assert action["confirmation_id"]
    assert action_response.status_code == 200
    assert action_result["status"] == "completed"
    assert action_result["interaction_event_id"]
    assert action_result["conversation_turn_id"]
    assert any(turn["id"] == action_result["conversation_turn_id"] and turn["turn_type"] == "observation" for turn in turns)
    assert any(turn["turn_type"] == "memory_candidate" and turn["memory_id"] == reflection_memory["id"] for turn in turns)
    assert reflection_memory["is_confirmed"] is False
    assert reflection_memory["status"] == "candidate"
    assert confirmed_memory["id"] == reflection_memory["id"]
    assert confirmed_memory["is_confirmed"] is True
    assert confirmed_memory["status"] == "confirmed"


def test_rich_surface_link_turn_uses_standard_target_payload() -> None:
    link = create_rich_surface_link(
        surface="ContractReviewArtifact",
        title="Open Full Review",
        target_type=RichSurfaceTargetType.drawer,
        source=RichSurfaceSource.user_action,
        artifact_id="artifact-1",
        target_title="Contract Review",
        channel="web",
        metadata={"interaction_id": "interaction-1"},
    )

    with TestClient(app) as client:
        workspace_id = client.get("/api/bootstrap").json()["workspace"]["id"]
        session = client.post("/api/conversations", json={"app_id": "contract-review-agent", "workspace_id": workspace_id}).json()
        turn = client.post(
            f"/api/conversations/{session['id']}/turns",
            json={
                "turn_type": "rich_surface_link",
                "role": "assistant",
                "content": link.title,
                "surface_type": link.surface,
                "surface_payload": link.model_dump(),
                "artifact_id": link.target.artifactId,
                "interaction_id": "interaction-1",
            },
        )

    assert turn.status_code == 200
    assert turn.json()["turn_type"] == "rich_surface_link"
    assert turn.json()["surface_payload_json"]["target"]["type"] == "drawer"
    assert turn.json()["surface_payload_json"]["target"]["source"] == "user_action"

    with pytest.raises(ValueError):
        RichSurfaceLink.model_validate(
            {
                "surface": "ContractReviewArtifact",
                "title": "Open Full Review",
                "target": {"type": "modal", "source": "automatic"},
            }
        )


def test_agent_context_builder_includes_ui_events_confirmed_memories_and_policy_decision() -> None:
    with TestClient(app):
        with SessionLocal() as db:
            workspace_id = "agent-context-workspace"
            project_id = "agent-context-project"
            artifact = Artifact(
                workspace_id=workspace_id,
                project_id=project_id,
                title="Context Artifact",
                type="contract_review",
                schema_json={"status": "ready", "blocks": [{"id": "risk_summary", "data": {"high_count": 1}}]},
            )
            memory = Memory(
                workspace_id=workspace_id,
                project_id=project_id,
                type="preference",
                content="Prefer negotiation-friendly revisions.",
                status="confirmed",
                is_confirmed=True,
            )
            interaction = UIInteractionEvent(
                workspace_id=workspace_id,
                project_id=project_id,
                artifact_id="artifact-context",
                event_type="artifact.action.approved",
                payload_json={"choice": "approve"},
            )
            confirmation = Confirmation(
                workspace_id=workspace_id,
                type="approval",
                title="Approve revision",
                description="Approve revision",
                status="pending",
                payload_json={},
            )
            db.add_all([artifact, memory, interaction, confirmation])
            db.commit()
            db.refresh(artifact)
            interaction_id = interaction.id
            session = ConversationSession(app_id="contract-review-agent", workspace_id=workspace_id, project_id=project_id, channel="web")
            db.add(session)
            db.commit()
            db.refresh(session)
            db.add(ConversationTurn(session_id=session.id, turn_type="user_message", role="user", content="Need safer language"))
            db.add(ConversationTurn(session_id=session.id, turn_type="observation", role="system", content="artifact.action.approved", interaction_id=interaction_id))
            db.commit()

            context = AgentContextBuilder(db).build(
                app_id="contract-review-agent",
                workspace_id=workspace_id,
                project_id=project_id,
                artifact_id=artifact.id,
                policy_context=InteractionContext(user_action="approve_revision"),
                session_id=session.id,
            )

    assert context["recent_ui_observations"][0]["event_type"] == "artifact.action.approved"
    assert context["confirmed_memories"][0]["content"] == "Prefer negotiation-friendly revisions."
    assert context["pending_confirmations"][0]["title"] == "Approve revision"
    assert context["active_artifact_summary"]["risk_summary"]["high_count"] == 1
    assert context["last_policy_decision"]["rule_id"] == "revision-approved-preview"
    assert context["recent_conversation_turns"][0]["content"] == "Need safer language"
    assert context["recent_user_messages"][0]["content"] == "Need safer language"
    assert context["recent_observation_turns"][0]["interaction_id"] == interaction_id
    assert context["context_budget"]["max_turn_content_chars"] == 500


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
    with SessionLocal() as db:
        session = db.query(ConversationSession).filter(ConversationSession.channel == "telegram", ConversationSession.external_thread_id == "8001").first()
        run = db.get(Run, body["run_id"])
        assert session is not None
        assert run.session_id == session.id
        assert db.query(ConversationTurn).filter(ConversationTurn.session_id == session.id, ConversationTurn.turn_type == "user_message").count() >= 1
        assert db.query(ConversationTurn).filter(ConversationTurn.session_id == session.id, ConversationTurn.turn_type == "rich_surface_link").count() >= 1


def test_telegram_callback_approves_confirmation_and_records_interaction() -> None:
    with TestClient(app) as client:
        bootstrap = client.get("/api/bootstrap").json()
        workspace = bootstrap["workspace"]
        with SessionLocal() as db:
            ConversationService(db).create_or_get_session(
                app_id="contract-review-agent",
                workspace_id=workspace["id"],
                channel=ConversationChannel.telegram,
                external_thread_id="8001",
                external_user_id="9001",
            )
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
            session = db.query(ConversationSession).filter(ConversationSession.channel == "telegram", ConversationSession.external_thread_id == "8001").first()
            observation_turn = (
                db.query(ConversationTurn)
                .filter(ConversationTurn.session_id == session.id, ConversationTurn.interaction_id == interaction.id, ConversationTurn.turn_type == "observation")
                .first()
                if session
                else None
            )

    assert response.status_code == 200
    assert body["confirmation_id"] == confirmation_id
    assert updated.status == "approved"
    assert updated.decision_json["decision"]["source"] == "telegram"
    assert interaction.event_type == "channel.telegram.approve_confirmation"
    assert interaction.payload_json["external_chat_id"] == "8001"
    assert observation_turn is not None


def test_telegram_callback_confirms_memory_candidate() -> None:
    with TestClient(app) as client:
        bootstrap = client.get("/api/bootstrap").json()
        workspace = bootstrap["workspace"]
        with SessionLocal() as db:
            ConversationService(db).create_or_get_session(
                app_id="contract-review-agent",
                workspace_id=workspace["id"],
                channel=ConversationChannel.telegram,
                external_thread_id="8001",
                external_user_id="9001",
            )
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
            observation_turn = db.query(ConversationTurn).filter(ConversationTurn.turn_type == "observation", ConversationTurn.memory_id.is_(None)).order_by(ConversationTurn.created_at.desc()).first()

    assert response.status_code == 200
    assert response.json()["memory_id"] == memory_id
    assert updated.status == "confirmed"
    assert updated.is_confirmed is True
    assert observation_turn is not None


def test_telegram_callback_reuses_artifact_action_runtime_when_context_is_present() -> None:
    workspace_id = "telegram-artifact-action-workspace"
    artifact_id = create_action_artifact(workspace_id=workspace_id)
    with TestClient(app) as client:
        with SessionLocal() as db:
            ConversationService(db).create_or_get_session(
                app_id="contract-review-agent",
                workspace_id=workspace_id,
                channel=ConversationChannel.telegram,
                external_thread_id="9009",
                external_user_id="1009",
            )

        response = client.post(
            "/api/channels/telegram/webhook",
            json={
                "update_id": 13,
                "callback_query": {
                    "id": "callback-4",
                    "from": {"id": 1009},
                    "message": {"message_id": 103, "chat": {"id": 9009}, "text": "Artifact action"},
                    "data": f"tilo:artifact_action:{artifact_id}|approve_block|summary",
                },
            },
        )
        body = response.json()

    assert response.status_code == 200
    assert body["status"] == "completed"
    assert body["action_result"]["interaction_event_id"]
    assert body["action_result"]["conversation_turn_id"]


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


def create_action_artifact(
    *,
    workspace_id: str,
    actions: list[dict] | None = None,
    blocks: list[dict] | None = None,
    run_id: str | None = None,
) -> str:
    with SessionLocal() as db:
        artifact = Artifact(
            workspace_id=workspace_id,
            run_id=run_id,
            title="Action Runtime Artifact",
            type="contract_review",
            schema_json={
                "version": "artifact_spec.v1",
                "artifact_type": "contract_review",
                "title": "Action Runtime Artifact",
                "status": "ready",
                "blocks": blocks
                or [
                    {
                        "id": "summary",
                        "type": "approval_card",
                        "data": {"title": "Approve"},
                        "actions": [
                            {
                                "id": "approve_block",
                                "label": "Approve block",
                                "action_type": "approve",
                                "confirmation_required": False,
                            }
                        ],
                    }
                ],
                "actions": actions or [],
                "run_id": run_id,
            },
        )
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        return artifact.id


def test_artifact_action_runtime_resolves_artifact_level_action() -> None:
    artifact_id = create_action_artifact(
        workspace_id="artifact-action-level-workspace",
        actions=[{"id": "export_json", "label": "Export JSON", "action_type": "export", "confirmation_required": False}],
    )

    with TestClient(app) as client:
        response = client.post(f"/api/artifacts/{artifact_id}/actions/export_json", json={"source": "web"})

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "noop"
    assert result["action_id"] == "export_json"
    assert result["interaction_event_id"]


def test_artifact_action_runtime_resolves_block_action_when_block_id_is_provided() -> None:
    artifact_id = create_action_artifact(workspace_id="artifact-action-block-workspace")

    with TestClient(app) as client:
        response = client.post(f"/api/artifacts/{artifact_id}/actions/approve_block", json={"block_id": "summary"})

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "completed"
    assert result["block_id"] == "summary"


def test_artifact_action_runtime_requires_block_id_for_duplicate_block_actions() -> None:
    artifact_id = create_action_artifact(
        workspace_id="artifact-action-duplicate-workspace",
        blocks=[
            {
                "id": "block_a",
                "type": "card",
                "data": {"content": "A"},
                "actions": [{"id": "choose", "label": "Choose", "action_type": "select", "confirmation_required": False}],
            },
            {
                "id": "block_b",
                "type": "card",
                "data": {"content": "B"},
                "actions": [{"id": "choose", "label": "Choose", "action_type": "select", "confirmation_required": False}],
            },
        ],
    )

    with TestClient(app) as client:
        missing_block = client.post(f"/api/artifacts/{artifact_id}/actions/choose", json={})
        with_block = client.post(f"/api/artifacts/{artifact_id}/actions/choose", json={"block_id": "block_b"})

    assert missing_block.status_code == 422
    assert "block_id is required" in missing_block.text
    assert with_block.status_code == 200
    assert with_block.json()["block_id"] == "block_b"


def test_artifact_action_runtime_unknown_action_returns_clear_error() -> None:
    artifact_id = create_action_artifact(workspace_id="artifact-action-unknown-workspace")

    with TestClient(app) as client:
        response = client.post(f"/api/artifacts/{artifact_id}/actions/missing_action", json={})

    assert response.status_code == 404
    assert "missing_action" in response.text


def test_artifact_action_runtime_approves_and_rejects_confirmation_bindings() -> None:
    workspace_id = "artifact-action-confirmation-workspace"
    with TestClient(app) as client:
        with SessionLocal() as db:
            confirmation = Confirmation(
                workspace_id=workspace_id,
                type="approval",
                title="Approve action",
                description="Approve action",
                status="pending",
                payload_json={},
            )
            rejected_confirmation = Confirmation(
                workspace_id=workspace_id,
                type="approval",
                title="Reject action",
                description="Reject action",
                status="pending",
                payload_json={},
            )
            db.add_all([confirmation, rejected_confirmation])
            db.commit()
            db.refresh(confirmation)
            db.refresh(rejected_confirmation)
            approve_artifact_id = create_action_artifact(
                workspace_id=workspace_id,
                blocks=[
                    {
                        "id": "approval",
                        "type": "approval_card",
                        "data": {"title": "Approve"},
                        "actions": [
                            {
                                "id": "approve_bound_confirmation",
                                "label": "Approve",
                                "action_type": "approve",
                                "confirmation_required": False,
                                "state_binding": {"entity_type": "confirmation", "entity_id": confirmation.id},
                            }
                        ],
                    }
                ],
            )
            reject_artifact_id = create_action_artifact(
                workspace_id=workspace_id,
                blocks=[
                    {
                        "id": "rejection",
                        "type": "approval_card",
                        "data": {"title": "Reject"},
                        "actions": [
                            {
                                "id": "reject_bound_confirmation",
                                "label": "Reject",
                                "action_type": "reject",
                                "confirmation_required": False,
                                "state_binding": {"entity_type": "confirmation", "entity_id": rejected_confirmation.id},
                            }
                        ],
                    }
                ],
            )
            confirmation_id = confirmation.id
            rejected_confirmation_id = rejected_confirmation.id

        approve = client.post(f"/api/artifacts/{approve_artifact_id}/actions/approve_bound_confirmation", json={"block_id": "approval"})
        reject = client.post(f"/api/artifacts/{reject_artifact_id}/actions/reject_bound_confirmation", json={"block_id": "rejection"})

    with SessionLocal() as db:
        approved = db.get(Confirmation, confirmation_id)
        rejected = db.get(Confirmation, rejected_confirmation_id)

    assert approve.status_code == 200
    assert approve.json()["confirmation_id"] == confirmation_id
    assert approved.status == "approved"
    assert reject.status_code == 200
    assert reject.json()["status"] == "rejected"
    assert rejected.status == "rejected"


def test_artifact_action_runtime_confirms_and_rejects_memory_bindings() -> None:
    workspace_id = "artifact-action-memory-workspace"
    with TestClient(app) as client:
        with SessionLocal() as db:
            confirm_memory = Memory(workspace_id=workspace_id, type="preference", content="Confirm me", status="candidate", is_confirmed=False)
            reject_memory = Memory(workspace_id=workspace_id, type="preference", content="Reject me", status="candidate", is_confirmed=False)
            db.add_all([confirm_memory, reject_memory])
            db.commit()
            db.refresh(confirm_memory)
            db.refresh(reject_memory)
            artifact_id = create_action_artifact(
                workspace_id=workspace_id,
                blocks=[
                    {
                        "id": "memory_confirm",
                        "type": "memory_candidate_card",
                        "data": {"content": "Confirm me"},
                        "actions": [
                            {
                                "id": "confirm_memory_action",
                                "label": "Remember",
                                "action_type": "confirm",
                                "confirmation_required": False,
                                "state_binding": {"entity_type": "memory", "entity_id": confirm_memory.id},
                            }
                        ],
                    },
                    {
                        "id": "memory_reject",
                        "type": "memory_candidate_card",
                        "data": {"content": "Reject me"},
                        "actions": [
                            {
                                "id": "reject_memory_action",
                                "label": "Reject",
                                "action_type": "reject",
                                "confirmation_required": False,
                                "state_binding": {"entity_type": "memory", "entity_id": reject_memory.id},
                            }
                        ],
                    },
                ],
            )
            confirm_memory_id = confirm_memory.id
            reject_memory_id = reject_memory.id

        confirm = client.post(f"/api/artifacts/{artifact_id}/actions/confirm_memory_action", json={"block_id": "memory_confirm"})
        reject = client.post(f"/api/artifacts/{artifact_id}/actions/reject_memory_action", json={"block_id": "memory_reject"})

    with SessionLocal() as db:
        confirmed = db.get(Memory, confirm_memory_id)
        rejected = db.get(Memory, reject_memory_id)

    assert confirm.status_code == 200
    assert confirm.json()["memory_id"] == confirm_memory_id
    assert confirmed.status == "confirmed"
    assert confirmed.is_confirmed is True
    assert reject.status_code == 200
    assert rejected.status == "rejected"
    assert rejected.is_confirmed is False


def test_artifact_action_runtime_create_memory_creates_unconfirmed_candidate_only() -> None:
    workspace_id = "artifact-action-create-memory-workspace"
    artifact_id = create_action_artifact(
        workspace_id=workspace_id,
        blocks=[
            {
                "id": "memory_candidate",
                "type": "memory_candidate_card",
                "data": {"content": "Prefer careful contract revisions.", "confidence": 0.81},
                "actions": [
                    {
                        "id": "create_memory_action",
                        "label": "Save candidate",
                        "action_type": "create_memory",
                        "confirmation_required": False,
                        "payload": {"type": "user_preference"},
                    }
                ],
            }
        ],
    )

    with TestClient(app) as client:
        response = client.post(f"/api/artifacts/{artifact_id}/actions/create_memory_action", json={"block_id": "memory_candidate"})
        memory_id = response.json()["memory_id"]

    with SessionLocal() as db:
        memory = db.get(Memory, memory_id)

    assert response.status_code == 200
    assert memory.status == "candidate"
    assert memory.is_confirmed is False
    assert memory.type == "user_preference"


def test_artifact_action_runtime_with_session_creates_interaction_and_observation_turn() -> None:
    workspace_id = "artifact-action-session-workspace"
    artifact_id = create_action_artifact(workspace_id=workspace_id)
    with TestClient(app) as client:
        session = client.post("/api/conversations", json={"app_id": "contract-review-agent", "workspace_id": workspace_id}).json()
        response = client.post(
            f"/api/artifacts/{artifact_id}/actions/approve_block",
            json={"block_id": "summary", "session_id": session["id"], "payload": {"api_key": "secret-value", "choice": "approve"}},
        )
        turns = client.get(f"/api/conversations/{session['id']}/turns").json()

    assert response.status_code == 200
    result = response.json()
    assert result["interaction_event_id"]
    assert result["conversation_turn_id"]
    assert any(turn["id"] == result["conversation_turn_id"] and turn["turn_type"] == "observation" for turn in turns)
    with SessionLocal() as db:
        event = db.get(UIInteractionEvent, result["interaction_event_id"])
        assert event.payload_json["request_payload"]["api_key"] == "[REDACTED]"


def test_artifact_action_runtime_continue_task_uses_conversation_message_flow() -> None:
    workspace_id = "artifact-action-continue-workspace"
    with TestClient(app) as client:
        session = client.post("/api/conversations", json={"app_id": "contract-review-agent", "workspace_id": workspace_id, "channel": "web"}).json()
        artifact_id = create_action_artifact(
            workspace_id=workspace_id,
            actions=[{"id": "continue_review", "label": "Continue", "action_type": "continue_task", "confirmation_required": False}],
        )
        response = client.post(
            f"/api/artifacts/{artifact_id}/actions/continue_review",
            json={"session_id": session["id"], "payload": {"content": "Continue with a conservative revision."}},
        )

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "completed"
    assert result["task_id"]
    assert result["run_id"]


def test_artifact_action_runtime_confirmation_required_tool_returns_pending_confirmation() -> None:
    workspace_id = "artifact-action-tool-workspace"
    with TestClient(app) as client:
        with SessionLocal() as db:
            task = Task(workspace_id=workspace_id, title="Tool task", input_message="Invoke tool")
            db.add(task)
            db.flush()
            run = Run(task_id=task.id, status="running")
            db.add(run)
            tool = Tool(workspace_id=workspace_id, name="High Risk Sender", type="mock_browser", permission_level="high")
            db.add(tool)
            db.commit()
            db.refresh(run)
            db.refresh(tool)
            artifact_id = create_action_artifact(
                workspace_id=workspace_id,
                run_id=run.id,
                actions=[
                    {
                        "id": "invoke_sender",
                        "label": "Invoke sender",
                        "action_type": "invoke_tool",
                        "confirmation_required": True,
                        "payload": {"tool_id": tool.id, "input": {"url": "https://example.com", "token": "secret-value"}},
                    }
                ],
            )
        response = client.post(f"/api/artifacts/{artifact_id}/actions/invoke_sender", json={})

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "pending_confirmation"
    assert result["confirmation_id"]
    assert result["tool_invocation_id"]


def test_artifact_action_runtime_unsupported_action_type_returns_safe_result() -> None:
    with SessionLocal() as db:
        artifact = Artifact(
            workspace_id="artifact-action-unsupported-workspace",
            title="Unsupported Action",
            type="contract_review",
            schema_json={
                "version": "artifact_spec.v1",
                "artifact_type": "contract_review",
                "title": "Unsupported Action",
                "blocks": [{"id": "summary", "type": "card", "data": {"content": "x"}}],
                "actions": [{"id": "bad_action", "label": "Bad", "action_type": "launch_missiles", "confirmation_required": False}],
            },
        )
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        artifact_id = artifact.id

    with TestClient(app) as client:
        response = client.post(f"/api/artifacts/{artifact_id}/actions/bad_action", json={})

    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert "Unsupported artifact action type" in response.json()["message"]


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
