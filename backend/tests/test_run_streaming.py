"""Tests for Phase 2 of the Surface Protocol refactor.

Covers:

1. Deterministic composer produces a valid SurfaceSpec for every intent.
2. `safe_compose` falls back when a composer raises.
3. `SurfaceTurnService.persist` stamps the spec ids and writes a
   ConversationTurn.
4. `RunManager.execute` walks the plan, emits multiple SurfaceTurns, and
   records `render_surface` trace entries.
5. The contract review demo flow now produces (a) one rich Artifact AND
   (b) at least one mini SurfaceTurn — proving streaming surfaces.
6. `GET /api/runs/{id}/surface-turns` returns the persisted list.
7. `GET /api/conversations/{id}/surface-turns` filters by session.
8. Backwards compatibility: the existing artifact pipeline still produces
   the same Artifact rows; existing artifact-action tests must keep passing
   (covered by running the full suite).
"""

from helpers import *  # noqa: F401,F403

from tilo.models import SurfaceTurn
from tilo.schemas.surface import (
    BudgetHint,
    SurfaceBlockType,
    SurfaceIntent,
    SurfaceSpecV1,
)
from tilo.services.interaction_policy.schemas import (
    InteractionDecision,
    InteractionDecisionType,
)
from tilo.services.surface.composer import (
    ComposerInput,
    DeterministicSurfaceComposer,
    SurfaceComposer,
    safe_compose,
)
from tilo.services.surface.persistence import SurfaceTurnService


# --------------------------------------------------------------------------- #
# 1. Deterministic composer per intent                                         #
# --------------------------------------------------------------------------- #


def _bare_task_and_run(workspace_id: str = "phase2-ws") -> tuple[Task, Run]:
    task = Task(workspace_id=workspace_id, title="Test task", input_message="Test task")
    run = Run(task_id="placeholder")
    # ids are stable enough for composer purposes; persistence stamps real ids.
    task.id = "task_test_1"
    run.id = "run_test_1"
    return task, run


def _decision_for(intent: SurfaceIntent, decision_type: InteractionDecisionType = InteractionDecisionType.mini_surface) -> InteractionDecision:
    return InteractionDecision(
        decision=decision_type,
        intent=intent,
        reason="phase2_test",
        rule_id="test_rule",
    )


@pytest.mark.parametrize(
    "intent,decision_type",
    [
        (SurfaceIntent.request_approval, InteractionDecisionType.mini_surface),
        (SurfaceIntent.collect_input, InteractionDecisionType.mini_surface),
        (SurfaceIntent.present_result, InteractionDecisionType.mini_surface),
        (SurfaceIntent.offer_choices, InteractionDecisionType.mini_surface),
        (SurfaceIntent.confirm_memory, InteractionDecisionType.mini_surface),
        (SurfaceIntent.show_progress, InteractionDecisionType.mini_surface),
        (SurfaceIntent.ask_clarification, InteractionDecisionType.mini_surface),
    ],
)
def test_deterministic_composer_produces_valid_spec_per_intent(
    intent: SurfaceIntent, decision_type: InteractionDecisionType
) -> None:
    task, run = _bare_task_and_run()
    payload = ComposerInput(
        intent=intent,
        decision=_decision_for(intent, decision_type),
        plan_step={"type": "generate_artifact", "risk_level": "high", "category": "liability"},
        plan_step_index=0,
        task=task,
        run=run,
    )
    result = DeterministicSurfaceComposer().compose(payload)
    assert isinstance(result.spec, SurfaceSpecV1)
    assert result.spec.intent == intent
    assert result.composer_mode == "deterministic"
    assert result.spec.fallback_text  # always non-empty
    # Round-trip dump+revalidate guarantees structural validity.
    SurfaceSpecV1.model_validate(result.spec.model_dump(by_alias=True))


def test_deterministic_request_approval_has_decision_block_with_actions() -> None:
    task, run = _bare_task_and_run()
    payload = ComposerInput(
        intent=SurfaceIntent.request_approval,
        decision=_decision_for(SurfaceIntent.request_approval),
        plan_step={"type": "generate_artifact", "risk_level": "high", "category": "liability"},
        plan_step_index=0,
        task=task,
        run=run,
    )
    spec = DeterministicSurfaceComposer().compose(payload).spec
    decision_blocks = [b for b in spec.blocks if b.type == SurfaceBlockType.decision]
    assert len(decision_blocks) == 1
    block = decision_blocks[0]
    action_ids = {a.id for a in block.actions}
    assert {"approve", "reject"} <= action_ids
    assert spec.budget_hint == BudgetHint.mini


def test_deterministic_escalate_to_rich_requires_artifact_or_falls_back() -> None:
    task, run = _bare_task_and_run()
    # Without artifact, escalate_to_rich gracefully falls back to present_result
    # (both produce valid specs; the runtime is responsible for never asking
    # for escalate_to_rich before an artifact exists).
    payload = ComposerInput(
        intent=SurfaceIntent.escalate_to_rich,
        decision=_decision_for(SurfaceIntent.escalate_to_rich, InteractionDecisionType.rich_surface),
        plan_step={"type": "generate_artifact"},
        plan_step_index=0,
        task=task,
        run=run,
        artifact_id=None,
        artifact_summary=None,
    )
    spec = DeterministicSurfaceComposer().compose(payload).spec
    SurfaceSpecV1.model_validate(spec.model_dump(by_alias=True))


def test_deterministic_escalate_to_rich_with_artifact_emits_artifact_link() -> None:
    task, run = _bare_task_and_run()
    payload = ComposerInput(
        intent=SurfaceIntent.escalate_to_rich,
        decision=_decision_for(SurfaceIntent.escalate_to_rich, InteractionDecisionType.rich_surface),
        plan_step={"type": "generate_artifact"},
        plan_step_index=0,
        task=task,
        run=run,
        artifact_id="art_123",
        artifact_summary={"title": "Contract Review", "summary": "12 risks", "artifact_id": "art_123"},
    )
    spec = DeterministicSurfaceComposer().compose(payload).spec
    types = [b.type for b in spec.blocks]
    assert SurfaceBlockType.artifact_link in types
    artifact_block = next(b for b in spec.blocks if b.type == SurfaceBlockType.artifact_link)
    assert artifact_block.data["artifact_id"] == "art_123"
    assert spec.budget_hint == BudgetHint.rich


# --------------------------------------------------------------------------- #
# 2. safe_compose falls back on errors                                         #
# --------------------------------------------------------------------------- #


class _BrokenComposer(SurfaceComposer):
    def compose(self, payload: ComposerInput):
        raise ValueError("boom")


def test_safe_compose_falls_back_to_deterministic_on_error() -> None:
    task, run = _bare_task_and_run()
    payload = ComposerInput(
        intent=SurfaceIntent.present_result,
        decision=_decision_for(SurfaceIntent.present_result),
        plan_step={"type": "ask_confirmation"},
        plan_step_index=0,
        task=task,
        run=run,
    )
    result = safe_compose(payload, _BrokenComposer())
    assert result.composer_mode == "deterministic_fallback"
    assert result.fallback_reason == "ValueError"
    assert isinstance(result.spec, SurfaceSpecV1)


# --------------------------------------------------------------------------- #
# 3. SurfaceTurnService.persist stamps ids and writes a ConversationTurn       #
# --------------------------------------------------------------------------- #


def test_surface_turn_service_persists_and_appends_conversation_turn() -> None:
    workspace_id = "phase2-persist-ws"
    with TestClient(app):
        with SessionLocal() as db:
            session = ConversationSession(app_id="contract-review-agent", workspace_id=workspace_id, channel="web")
            db.add(session)
            db.commit()
            db.refresh(session)

            task = Task(workspace_id=workspace_id, title="t", input_message="t")
            db.add(task)
            db.flush()
            run = Run(task_id=task.id, session_id=session.id)
            db.add(run)
            db.commit()
            db.refresh(task)
            db.refresh(run)

            payload = ComposerInput(
                intent=SurfaceIntent.request_approval,
                decision=_decision_for(SurfaceIntent.request_approval),
                plan_step={"type": "generate_artifact", "risk_level": "high", "category": "liability"},
                plan_step_index=3,
                task=task,
                run=run,
            )
            composed = DeterministicSurfaceComposer().compose(payload)
            turn_row = SurfaceTurnService(db).persist(
                task=task,
                run=run,
                composed=composed,
                decision=_decision_for(SurfaceIntent.request_approval),
                plan_step=payload.plan_step,
                plan_step_index=3,
                ordinal=0,
                session_id=session.id,
            )

            # Spec ids stamped to row id.
            assert turn_row.surface_spec_json["surface_id"] == turn_row.id
            assert turn_row.surface_spec_json["turn_id"] == turn_row.id
            assert turn_row.intent == SurfaceIntent.request_approval.value
            assert turn_row.composer_mode == "deterministic"

            # Conversation turn written.
            turns = list(db.query(ConversationTurn).filter(ConversationTurn.session_id == session.id))
            mini = [t for t in turns if t.turn_type == "mini_surface"]
            assert len(mini) == 1
            assert mini[0].surface_payload_json["intent"] == "request_approval"


# --------------------------------------------------------------------------- #
# 4-5. RunManager streaming surface loop                                       #
# --------------------------------------------------------------------------- #


def test_run_manager_emits_multiple_surface_turns_for_contract_review() -> None:
    workspace_id = "phase2-stream-ws"
    with TestClient(app):
        with SessionLocal() as db:
            session = ConversationSession(app_id="contract-review-agent", workspace_id=workspace_id, channel="web")
            db.add(session)
            db.commit()
            db.refresh(session)
            session_id = session.id

            task = Task(
                workspace_id=workspace_id,
                title="Review this AI services contract liability clauses.",
                input_message="Review this AI services contract liability clauses.",
            )
            db.add(task)
            db.flush()
            run = Run(task_id=task.id, session_id=session_id)
            db.add(run)
            db.commit()
            db.refresh(task)
            db.refresh(run)
            run_id = run.id

            result = RunManager(db).execute(task, run, agent=None, session_id=session_id)

        # Result includes streamed surface_turns.
        assert "surface_turns" in result
        assert len(result["surface_turns"]) >= 1

        with SessionLocal() as db:
            run = db.get(Run, run_id)
            assert run is not None
            plan = run.plan_json or {}
            surface_turn_ids = plan.get("surface_turn_ids") or []
            assert len(surface_turn_ids) >= 1

            # All persisted SurfaceTurns are for this run, in ordinal order.
            turns = (
                db.query(SurfaceTurn)
                .filter(SurfaceTurn.run_id == run_id)
                .order_by(SurfaceTurn.ordinal.asc())
                .all()
            )
            assert [t.id for t in turns] == surface_turn_ids
            assert all(t.session_id == session_id for t in turns)
            assert all(t.composer_mode in {"deterministic", "deterministic_fallback"} for t in turns)
            # Specs round-trip cleanly.
            for t in turns:
                SurfaceSpecV1.model_validate(t.surface_spec_json)

            # The contract-review run MUST produce at least one
            # request_approval mini surface (high-risk policy rule fires).
            intents = [t.intent for t in turns]
            assert SurfaceIntent.request_approval.value in intents

            # `render_surface` trace entries match the persisted turns count.
            trace = (
                db.query(TraceStep)
                .filter(TraceStep.run_id == run_id, TraceStep.step_type == "render_surface")
                .all()
            )
            assert len(trace) == len(turns)


def test_run_manager_still_produces_artifact_for_backward_compat() -> None:
    """The Artifact pipeline must not regress: contract review still emits
    a structured Artifact row that downstream artifact-action tests rely on."""
    workspace_id = "phase2-artifact-ws"
    with TestClient(app):
        with SessionLocal() as db:
            session = ConversationSession(app_id="contract-review-agent", workspace_id=workspace_id, channel="web")
            db.add(session)
            db.commit()
            db.refresh(session)
            session_id = session.id

            task = Task(
                workspace_id=workspace_id,
                title="Review this contract for liability.",
                input_message="Review this contract for liability.",
            )
            db.add(task)
            db.flush()
            run = Run(task_id=task.id, session_id=session_id)
            db.add(run)
            db.commit()
            db.refresh(task)
            db.refresh(run)
            run_id = run.id

            result = RunManager(db).execute(task, run, agent=None, session_id=session_id)
            artifacts = result["artifacts"]
            assert len(artifacts) == 1
            artifact_id = artifacts[0].id
            artifact_type = artifacts[0].type
            assert artifact_type == "contract_review"

        with SessionLocal() as db:
            linked = (
                db.query(SurfaceTurn)
                .filter(SurfaceTurn.run_id == run_id, SurfaceTurn.artifact_id == artifact_id)
                .all()
            )
            assert len(linked) >= 1


# --------------------------------------------------------------------------- #
# 6-7. HTTP endpoints                                                          #
# --------------------------------------------------------------------------- #


def test_run_surface_turns_endpoint_returns_persisted_turns() -> None:
    workspace_id = "phase2-http-run-ws"
    with TestClient(app) as client:
        bootstrap = client.get("/api/bootstrap").json()
        ws_id = bootstrap["workspace"]["id"]
        session = client.post(
            "/api/conversations",
            json={"app_id": "contract-review-agent", "workspace_id": ws_id, "channel": "web"},
        ).json()
        message = client.post(
            f"/api/conversations/{session['id']}/messages",
            json={"content": "Review the contract liability section.", "attachments": []},
        ).json()

        run_id = message["run_id"]
        response = client.get(f"/api/runs/{run_id}/surface-turns")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert all("surface_spec_json" in t for t in body)
    # Ordinals are 0..N-1, ascending.
    ordinals = [t["ordinal"] for t in body]
    assert ordinals == sorted(ordinals)


def test_session_surface_turns_endpoint_filters_by_session() -> None:
    with TestClient(app) as client:
        bootstrap = client.get("/api/bootstrap").json()
        ws_id = bootstrap["workspace"]["id"]
        session = client.post(
            "/api/conversations",
            json={"app_id": "contract-review-agent", "workspace_id": ws_id, "channel": "web"},
        ).json()
        client.post(
            f"/api/conversations/{session['id']}/messages",
            json={"content": "Review this contract.", "attachments": []},
        )
        response = client.get(f"/api/conversations/{session['id']}/surface-turns")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert all(t["session_id"] == session["id"] for t in body)
    assert len(body) >= 1


def test_session_surface_turns_endpoint_404_for_missing_session() -> None:
    with TestClient(app) as client:
        response = client.get("/api/conversations/does-not-exist/surface-turns")
    assert response.status_code == 404
