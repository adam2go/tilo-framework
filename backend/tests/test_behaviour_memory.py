"""Tests for behaviour-aware memory (refactored from UI-coupled to action-stream).

Verifies:

1. Repeated rejections of the same `(operation, category)` produce a
   `preference_negative` candidate; `block_id` is recorded for audit but
   does NOT participate in the dedup signature.
2. Repeated selects of the same option value produce
   `preference_positive`.
3. An edit action on a memory-bound region produces
   `memory_update_proposed`.
4. Behaviour signatures de-dup against existing memories.
5. `MemoryExtractionService` persists behaviour candidates as
   `source_type="ui_behaviour"` alongside the task-experience candidate.
6. Full end-to-end through `RunManager` + HTTP.
7. No double-emit on consecutive runs over the same event window.
"""

from helpers import *  # noqa: F401,F403

from tilo.services.memory.behaviour import (
    REJECT_THRESHOLD,
    SELECT_THRESHOLD,
    BehaviourMemoryAnalyzer,
)
from tilo.services.memory.extraction import MemoryExtractionService


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _make_event(
    db,
    *,
    workspace_id: str,
    event_type: str,
    block_id: str | None = None,
    artifact_id: str | None = None,
    payload: dict | None = None,
    project_id: str | None = None,
) -> UIInteractionEvent:
    event = UIInteractionEvent(
        workspace_id=workspace_id,
        project_id=project_id,
        artifact_id=artifact_id,
        block_id=block_id,
        event_type=event_type,
        payload_json=payload or {},
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def _reject_payload(*, operation: str, risk_level: str = "high", category: str = "liability") -> dict:
    return {
        "request_payload": {"operation": operation, "risk_level": risk_level, "category": category},
        "action_payload": {"operation": operation, "risk_level": risk_level, "category": category},
    }


# --------------------------------------------------------------------------- #
# 1. Repeated rejects on the same operation/category                          #
# --------------------------------------------------------------------------- #


def test_analyzer_emits_preference_negative_on_repeated_operation_rejects() -> None:
    workspace_id = "phase4-rejects-ws"
    with TestClient(app):
        with SessionLocal() as db:
            # Three rejects of the same operation, but on three DIFFERENT
            # block_ids — proving signatures are operation-based, not UI-based.
            events = [
                _make_event(
                    db,
                    workspace_id=workspace_id,
                    event_type="artifact.action.rejected",
                    block_id=f"block_{i}",
                    artifact_id=f"art_{i}",
                    payload=_reject_payload(operation="propose_revision", category="liability"),
                )
                for i in range(REJECT_THRESHOLD)
            ]

            candidates = BehaviourMemoryAnalyzer(db).analyse(
                workspace_id=workspace_id, project_id=None, events=events
            )

            assert len(candidates) == 1
            cand = candidates[0]
            assert cand.memory_type == "preference_negative"
            assert cand.signature == "reject:propose_revision:liability"
            payload = cand.structured_payload
            assert payload["operation"] == "propose_revision"
            assert payload["category"] == "liability"
            assert payload["reject_count"] == REJECT_THRESHOLD
            # block_ids recorded for audit only.
            assert sorted(payload["block_ids_seen"]) == [f"block_{i}" for i in range(REJECT_THRESHOLD)]


def test_analyzer_does_not_fire_below_reject_threshold() -> None:
    workspace_id = "phase4-rejects-low-ws"
    with TestClient(app):
        with SessionLocal() as db:
            events = [
                _make_event(
                    db,
                    workspace_id=workspace_id,
                    event_type="artifact.action.rejected",
                    block_id="b",
                    payload=_reject_payload(operation="x"),
                )
                for _ in range(REJECT_THRESHOLD - 1)
            ]
            candidates = BehaviourMemoryAnalyzer(db).analyse(
                workspace_id=workspace_id, project_id=None, events=events
            )
            assert candidates == []


def test_analyzer_skips_rejects_without_operation() -> None:
    """Rejects without an `operation` payload have no behavioural meaning."""
    workspace_id = "phase4-rejects-noop-ws"
    with TestClient(app):
        with SessionLocal() as db:
            events = [
                _make_event(
                    db,
                    workspace_id=workspace_id,
                    event_type="artifact.action.rejected",
                    block_id="b",
                    payload={},  # no operation
                )
                for _ in range(REJECT_THRESHOLD)
            ]
            candidates = BehaviourMemoryAnalyzer(db).analyse(
                workspace_id=workspace_id, project_id=None, events=events
            )
            assert candidates == []


# --------------------------------------------------------------------------- #
# 2. Repeated selects                                                         #
# --------------------------------------------------------------------------- #


def test_analyzer_emits_preference_positive_on_repeated_selects() -> None:
    workspace_id = "phase4-selects-ws"
    with TestClient(app):
        with SessionLocal() as db:
            events = [
                _make_event(
                    db,
                    workspace_id=workspace_id,
                    event_type="artifact.option.selected",
                    block_id=f"b_{i}",
                    payload={"request_payload": {"value": "conservative"}},
                )
                for i in range(SELECT_THRESHOLD)
            ]
            candidates = BehaviourMemoryAnalyzer(db).analyse(
                workspace_id=workspace_id, project_id=None, events=events
            )
            assert len(candidates) == 1
            cand = candidates[0]
            assert cand.memory_type == "preference_positive"
            assert cand.signature == "select:conservative"
            assert cand.structured_payload["option_value"] == "conservative"


# --------------------------------------------------------------------------- #
# 3. Memory edit proposal                                                      #
# --------------------------------------------------------------------------- #


def test_analyzer_emits_memory_update_on_edit_of_memory_binding() -> None:
    workspace_id = "phase4-edit-ws"
    with TestClient(app):
        with SessionLocal() as db:
            event = _make_event(
                db,
                workspace_id=workspace_id,
                event_type="artifact.block.edited",
                block_id="r",
                payload={"state_binding": {"entity_type": "memory", "entity_id": "mem_42"}},
            )
            candidates = BehaviourMemoryAnalyzer(db).analyse(
                workspace_id=workspace_id, project_id=None, events=[event]
            )
            assert len(candidates) == 1
            cand = candidates[0]
            assert cand.memory_type == "memory_update_proposed"
            assert cand.signature == "memory_edit:mem_42"


# --------------------------------------------------------------------------- #
# 4. Dedup via behaviour_signature                                            #
# --------------------------------------------------------------------------- #


def test_analyzer_dedupes_against_existing_behaviour_memory() -> None:
    workspace_id = "phase4-dedup-ws"
    with TestClient(app):
        with SessionLocal() as db:
            existing = Memory(
                workspace_id=workspace_id,
                type="preference_negative",
                content="prior",
                source_type="ui_behaviour",
                status="candidate",
                is_confirmed=False,
                structured_payload={"behaviour_signature": "reject:propose_revision:liability"},
            )
            db.add(existing)
            db.commit()

            events = [
                _make_event(
                    db,
                    workspace_id=workspace_id,
                    event_type="artifact.action.rejected",
                    block_id=f"b_{i}",
                    payload=_reject_payload(operation="propose_revision", category="liability"),
                )
                for i in range(REJECT_THRESHOLD)
            ]
            candidates = BehaviourMemoryAnalyzer(db).analyse(
                workspace_id=workspace_id, project_id=None, events=events
            )
            assert candidates == []  # suppressed


# --------------------------------------------------------------------------- #
# 5. MemoryExtractionService persists behaviour candidates                    #
# --------------------------------------------------------------------------- #


def test_extraction_service_persists_behaviour_candidates_alongside_task_memory() -> None:
    workspace_id = "phase4-extract-ws"
    with TestClient(app):
        with SessionLocal() as db:
            task = Task(workspace_id=workspace_id, title="Review contract.", input_message="Review contract.")
            db.add(task)
            db.flush()
            run = Run(task_id=task.id)
            db.add(run)
            db.flush()
            artifact = Artifact(
                workspace_id=workspace_id,
                task_id=task.id,
                run_id=run.id,
                type="contract_review",
                title="Review",
                schema_json={
                    "version": "artifact_spec.v1",
                    "artifact_type": "contract_review",
                    "title": "x",
                    "blocks": [{"id": "x", "type": "markdown", "data": {"content": "x"}}],
                },
            )
            db.add(artifact)
            for _ in range(REJECT_THRESHOLD):
                _make_event(
                    db,
                    workspace_id=workspace_id,
                    event_type="artifact.action.rejected",
                    block_id="risk_summary",
                    artifact_id=artifact.id,
                    payload=_reject_payload(operation="propose_revision", category="liability"),
                )
            db.commit()
            db.refresh(task)
            db.refresh(run)
            db.refresh(artifact)

            run_id = run.id

            recorder = TraceRecorder(db)
            candidates = MemoryExtractionService(db, recorder).extract_candidates(task, run, artifact)

            assert len(candidates) == 2
            assert {m.source_type for m in candidates} == {"run", "ui_behaviour"}

            behaviour = next(m for m in candidates if m.source_type == "ui_behaviour")
            assert behaviour.type == "preference_negative"
            assert behaviour.is_confirmed is True  # auto-confirmed
            assert behaviour.status == "confirmed"
            payload = behaviour.structured_payload or {}
            assert payload.get("rule") == "repeated_rejects"
            assert payload.get("behaviour_signature") == "reject:propose_revision:liability"

        # Trace records the behaviour candidates by rule + signature.
        with SessionLocal() as db:
            entries = (
                db.query(TraceStep)
                .filter(TraceStep.run_id == run_id, TraceStep.step_type == "extract_memory")
                .all()
            )
            assert len(entries) == 1
            output = entries[0].output_json or {}
            assert any(b["rule"] == "repeated_rejects" for b in output.get("behaviour_candidates", []))


# --------------------------------------------------------------------------- #
# 6-7. End-to-end through RunManager + HTTP                                   #
# --------------------------------------------------------------------------- #


def test_run_manager_emits_behaviour_memory_candidate_after_seeded_rejects() -> None:
    with TestClient(app) as client:
        bootstrap = client.get("/api/bootstrap").json()
        ws_id = bootstrap["workspace"]["id"]

        with SessionLocal() as db:
            for i in range(REJECT_THRESHOLD):
                _make_event(
                    db,
                    workspace_id=ws_id,
                    event_type="artifact.action.rejected",
                    block_id=f"surface_{i}",
                    payload=_reject_payload(operation="propose_revision", category="liability"),
                )

        session = client.post(
            "/api/conversations",
            json={"app_id": "contract-review-agent", "workspace_id": ws_id, "channel": "web"},
        ).json()
        client.post(
            f"/api/conversations/{session['id']}/messages",
            json={"content": "Review the contract liability section.", "attachments": []},
        )

        memories = client.get(f"/api/memories?workspace_id={ws_id}").json()

    behaviour = [m for m in memories if m.get("type") == "preference_negative"]
    assert len(behaviour) >= 1
    payload = behaviour[0].get("structured_payload") or {}
    assert payload.get("behaviour_signature") == "reject:propose_revision:liability"


def test_run_manager_does_not_double_emit_behaviour_memory_on_consecutive_runs() -> None:
    with TestClient(app) as client:
        bootstrap = client.get("/api/bootstrap").json()
        ws_id = bootstrap["workspace"]["id"]

        with SessionLocal() as db:
            for _ in range(REJECT_THRESHOLD):
                _make_event(
                    db,
                    workspace_id=ws_id,
                    event_type="artifact.action.rejected",
                    block_id="x",
                    payload=_reject_payload(operation="dedup_op", category="dedup_cat"),
                )

        session = client.post(
            "/api/conversations",
            json={"app_id": "contract-review-agent", "workspace_id": ws_id, "channel": "web"},
        ).json()

        client.post(
            f"/api/conversations/{session['id']}/messages",
            json={"content": "first goal", "attachments": []},
        )
        first = [
            m for m in client.get(f"/api/memories?workspace_id={ws_id}").json()
            if (m.get("structured_payload") or {}).get("behaviour_signature") == "reject:dedup_op:dedup_cat"
        ]

        client.post(
            f"/api/conversations/{session['id']}/messages",
            json={"content": "second goal", "attachments": []},
        )
        second = [
            m for m in client.get(f"/api/memories?workspace_id={ws_id}").json()
            if (m.get("structured_payload") or {}).get("behaviour_signature") == "reject:dedup_op:dedup_cat"
        ]

    assert len(first) == 1
    assert len(second) == 1
