import os
import tempfile
from pathlib import Path

db_path = Path(tempfile.gettempdir()) / "tilo_smoke_test.db"
if db_path.exists():
    db_path.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Run, Task, TraceStep  # noqa: E402
from app.services.agent_runtime.run_manager import RunManager  # noqa: E402
from app.services.agent_runtime.state_machine import InvalidStateTransition, RunStateMachine  # noqa: E402
from app.services.artifact.generator import ArtifactGenerator  # noqa: E402
from app.schemas.artifact import ArtifactSpecV1  # noqa: E402
from app.services.trace.recorder import TraceRecorder  # noqa: E402


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


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
