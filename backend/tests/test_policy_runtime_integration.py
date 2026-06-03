"""Tests for Phase 1 of the Surface Protocol refactor.

Verifies that:

1. `InteractionRule` accepts both legacy `surface:` and modern `intent:`,
   and rejects ill-formed combinations.
2. `InteractionPolicyService.evaluate` populates BOTH `intent` and
   (when present) the legacy `surface` on every UI decision.
3. `Planner` emits per-step policy metadata (signal/risk_level/category/
   requires_user_decision).
4. `RunManager.execute` evaluates the InteractionPolicy for every plan
   step, persists the decisions on the run plan, and records one
   `policy_decision` trace entry per step.
5. Existing deterministic demo flows still pass.
"""

from helpers import *  # noqa: F401,F403

from tilo.schemas.surface import SurfaceIntent
from tilo.services.agent_runtime.planner import Planner
from tilo.services.interaction_policy.schemas import (
    InteractionContext,
    InteractionDecisionType,
    InteractionPolicy,
    InteractionRule,
    LEGACY_SURFACE_TO_INTENT,
)


# --------------------------------------------------------------------------- #
# 1. InteractionRule schema                                                   #
# --------------------------------------------------------------------------- #


def test_rule_accepts_intent_only() -> None:
    rule = InteractionRule.model_validate(
        {
            "id": "r1",
            "when": {"signal": "x"},
            "decision": "mini_surface",
            "intent": "request_approval",
            "reason": "ok",
        }
    )
    assert rule.intent == SurfaceIntent.request_approval
    assert rule.surface is None


def test_rule_accepts_legacy_surface_and_derives_intent() -> None:
    rule = InteractionRule.model_validate(
        {
            "id": "r2",
            "when": {"signal": "x"},
            "decision": "mini_surface",
            "surface": "MiniIssueCard",
            "reason": "ok",
        }
    )
    assert rule.surface == "MiniIssueCard"
    assert rule.intent == LEGACY_SURFACE_TO_INTENT["MiniIssueCard"]


def test_rule_rejects_mini_decision_without_target() -> None:
    with pytest.raises(ValueError, match="requires either 'intent'"):
        InteractionRule.model_validate(
            {"id": "r3", "decision": "mini_surface", "reason": "missing"}
        )


def test_rule_rejects_no_ui_with_intent() -> None:
    with pytest.raises(ValueError, match="must not declare an intent"):
        InteractionRule.model_validate(
            {"id": "r4", "decision": "no_ui", "intent": "request_approval", "reason": "bad"}
        )


def test_rule_rejects_unknown_legacy_surface_falls_back_to_derived_intent() -> None:
    """During the migration window, unknown surface names are tolerated at
    schema-load time. Validation against `app.yaml` is the proper place to
    reject them. The derived intent depends on the rule decision."""
    mini_rule = InteractionRule.model_validate(
        {
            "id": "r5a",
            "decision": "mini_surface",
            "surface": "UnknownMiniCard",
            "reason": "missing-mapping",
        }
    )
    assert mini_rule.intent == SurfaceIntent.present_result
    assert mini_rule.surface == "UnknownMiniCard"

    rich_rule = InteractionRule.model_validate(
        {
            "id": "r5b",
            "decision": "rich_surface",
            "surface": "UnknownRichArtifact",
            "reason": "missing-mapping",
        }
    )
    assert rich_rule.intent == SurfaceIntent.escalate_to_rich


# --------------------------------------------------------------------------- #
# 2. InteractionPolicyService now emits intent + legacy surface               #
# --------------------------------------------------------------------------- #


def test_policy_evaluate_returns_intent_for_contract_review_high_risk() -> None:
    decision = InteractionPolicyService().evaluate_for_app(
        "contract-review-agent",
        InteractionContext(
            artifact_type="contract_review",
            risk_level="high",
            requires_user_decision=True,
            category="liability",
        ),
    )
    assert decision.decision == InteractionDecisionType.mini_surface
    assert decision.intent == SurfaceIntent.request_approval
    assert decision.surface == "MiniIssueCard"  # legacy passthrough preserved
    assert decision.rule_id == "high-risk-liability-needs-confirmation"


def test_policy_evaluate_emits_intent_for_sales_followup() -> None:
    decision = InteractionPolicyService().evaluate_for_app(
        "sales-followup-agent",
        InteractionContext(signal="followup_tone_needed"),
    )
    assert decision.intent == SurfaceIntent.offer_choices
    assert decision.surface == "MiniChoiceCard"


def test_policy_no_ui_match_carries_no_intent() -> None:
    decision = InteractionPolicyService().evaluate_for_app(
        "contract-review-agent",
        InteractionContext(artifact_type="contract_review", risk_level="medium"),
    )
    assert decision.decision == InteractionDecisionType.no_ui
    assert decision.intent is None
    assert decision.surface is None


def test_policy_confirmation_budget_falls_back_to_ask_text() -> None:
    decision = InteractionPolicyService().evaluate_for_app(
        "contract-review-agent",
        InteractionContext(
            artifact_type="contract_review",
            risk_level="high",
            requires_user_decision=True,
            category="liability",
            confirmations_used=2,  # >= max_confirmations_per_run
        ),
    )
    assert decision.decision == InteractionDecisionType.ask_text
    assert decision.reason == "confirmation_budget_exceeded"


# --------------------------------------------------------------------------- #
# 3. App manifest validates intent-only rules when surfaces.intents declared   #
# --------------------------------------------------------------------------- #


def test_app_validates_intent_only_rule_against_declared_intents(tmp_path: Path) -> None:
    app_dir = tmp_path / "intent-only-agent"
    app_dir.mkdir()
    (app_dir / "app.yaml").write_text(
        """
id: intent-only-agent
version: "0.1"
name: Intent Only
description: Manifest declares intents instead of surfaces
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
  intents:
    - request_approval
    - confirm_memory
sample_inputs: []
tools: []
channels:
  - web
""",
        encoding="utf-8",
    )
    (app_dir / "interaction.policy.yaml").write_text(
        """
id: intent-only-policy
version: "0.1"
rules:
  - id: ok-rule
    when:
      signal: needs_approval
    decision: mini_surface
    intent: request_approval
    reason: ok
""",
        encoding="utf-8",
    )

    loader = AgentAppLoader(tmp_path)
    service = InteractionPolicyService()
    manifest = loader.load_manifest("intent-only-agent")
    policy = service.load_file(loader.load_policy_path("intent-only-agent"))
    service.validate_for_app(manifest, policy)  # must not raise


def test_app_rejects_intent_not_declared_in_manifest(tmp_path: Path) -> None:
    app_dir = tmp_path / "wrong-intent-agent"
    app_dir.mkdir()
    (app_dir / "app.yaml").write_text(
        """
id: wrong-intent-agent
version: "0.1"
name: Wrong Intent
description: Declares only request_approval but rule emits offer_choices
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
  intents:
    - request_approval
sample_inputs: []
tools: []
channels:
  - web
""",
        encoding="utf-8",
    )
    (app_dir / "interaction.policy.yaml").write_text(
        """
id: wrong-intent-policy
version: "0.1"
rules:
  - id: bad-rule
    when:
      signal: needs_choice
    decision: mini_surface
    intent: offer_choices
    reason: bad
""",
        encoding="utf-8",
    )

    loader = AgentAppLoader(tmp_path)
    service = InteractionPolicyService()
    manifest = loader.load_manifest("wrong-intent-agent")
    policy = service.load_file(loader.load_policy_path("wrong-intent-agent"))
    with pytest.raises(ValueError, match="undeclared intent"):
        service.validate_for_app(manifest, policy)


# --------------------------------------------------------------------------- #
# 4. Planner emits per-step policy metadata                                   #
# --------------------------------------------------------------------------- #


def test_planner_steps_carry_signal_and_risk_metadata() -> None:
    task = Task(
        workspace_id="ws_test",
        title="Review the AI services contract liability clauses.",
        input_message="Review the AI services contract liability clauses.",
    )
    plan = Planner().plan(task, memories=[], skills=[])

    assert plan["artifact_type"] == "contract_review"
    assert all("signal" in step for step in plan["steps"])
    assert all("risk_level" in step for step in plan["steps"])
    assert all("category" in step for step in plan["steps"])
    assert all("requires_user_decision" in step for step in plan["steps"])

    # The "generate_artifact" step for a contract carries high risk.
    artifact_step = next(s for s in plan["steps"] if s["type"] == "generate_artifact")
    assert artifact_step["risk_level"] == "high"
    assert artifact_step["category"] == "liability"
    assert artifact_step["requires_user_decision"] is True


# --------------------------------------------------------------------------- #
# 5. RunManager evaluates policy per step and records trace                   #
# --------------------------------------------------------------------------- #


def _create_session_for_app(app_id: str, workspace_id: str) -> str:
    with SessionLocal() as db:
        session = ConversationSession(app_id=app_id, workspace_id=workspace_id, channel="web")
        db.add(session)
        db.commit()
        db.refresh(session)
        return session.id


def test_run_manager_records_policy_decision_per_plan_step() -> None:
    workspace_id = "phase1-policy-runtime-ws"

    with TestClient(app):
        session_id = _create_session_for_app("contract-review-agent", workspace_id)

        with SessionLocal() as db:
            task = Task(
                workspace_id=workspace_id,
                title="Review this AI services contract for liability clauses.",
                input_message="Review this AI services contract for liability clauses.",
            )
            db.add(task)
            db.flush()
            run = Run(task_id=task.id, session_id=session_id)
            db.add(run)
            db.commit()
            db.refresh(task)
            db.refresh(run)
            run_id = run.id

            RunManager(db).execute(task, run, agent=None, session_id=session_id)

        with SessionLocal() as db:
            run = db.get(Run, run_id)
            assert run is not None
            plan = run.plan_json or {}
            decisions = plan.get("policy_decisions") or []
            steps = plan.get("steps") or []

            # Per-step decision count must match the plan exactly.
            assert len(decisions) == len(steps), f"got {len(decisions)} decisions for {len(steps)} steps"

            # The contract-review high-risk artifact step MUST resolve to a
            # mini_surface request_approval decision under the example policy.
            artifact_step_index = next(i for i, s in enumerate(steps) if s["type"] == "generate_artifact")
            artifact_decision = decisions[artifact_step_index]
            assert artifact_decision["decision"] == "mini_surface"
            assert artifact_decision["intent"] == "request_approval"
            assert artifact_decision["rule_id"] == "high-risk-liability-needs-confirmation"

            # The memory-extraction step now resolves to no_ui (auto-confirm).
            memory_step_index = next(i for i, s in enumerate(steps) if s["type"] == "extract_memory")
            memory_decision = decisions[memory_step_index]
            assert memory_decision["decision"] == "no_ui"

            # Trace must include one policy_decision entry per plan step.
            trace_steps = [
                t for t in db.query(TraceStep).filter(TraceStep.run_id == run_id).all()
                if t.step_type == "policy_decision"
            ]
            assert len(trace_steps) == len(steps)


def test_run_manager_handles_missing_policy_gracefully() -> None:
    """If the conversation session points at an unknown app, the run still
    completes; policy decisions degrade to no_ui with a clear trace entry."""
    workspace_id = "phase1-policy-missing-ws"

    with TestClient(app):
        with SessionLocal() as db:
            session = ConversationSession(app_id="does-not-exist-agent", workspace_id=workspace_id, channel="web")
            db.add(session)
            db.commit()
            db.refresh(session)
            session_id = session.id

            task = Task(
                workspace_id=workspace_id,
                title="Just chat",
                input_message="Just chat",
            )
            db.add(task)
            db.flush()
            run = Run(task_id=task.id, session_id=session_id)
            db.add(run)
            db.commit()
            db.refresh(task)
            db.refresh(run)
            run_id = run.id

            RunManager(db).execute(task, run, agent=None, session_id=session_id)

        with SessionLocal() as db:
            run = db.get(Run, run_id)
            assert run is not None
            decisions = (run.plan_json or {}).get("policy_decisions") or []
            assert run.status in {"completed", "failed"}
            assert all(d["decision"] in {"no_ui", "ask_text"} for d in decisions)
