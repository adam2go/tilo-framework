import os
import tempfile
from pathlib import Path

db_path = Path(tempfile.gettempdir()) / "tilo_smoke_test.db"
if db_path.exists():
    db_path.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


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
    assert artifacts[0]["schema_json"]["actions"]
    assert artifacts[0]["schema_json"]["actions"][0]["confirmation_required"] is True
    assert artifacts[0]["schema_json"]["actions"][0]["confirmation_id"]
    assert any(step["step_type"] == "recall_memory" for step in trace)
    assert any(step["step_type"] == "generate_artifact" for step in trace)
    assert recall_events and recall_events[0]["strategy"] == "hybrid_v0.2"
    assert any(event["event_type"] == "candidate_created" for event in write_events)
    assert confirmations
    assert any(memory["status"] == "candidate" and memory["is_confirmed"] is False for memory in memories)
    assert metrics["success"] is True
    assert metrics["artifact_count"] == 1
    assert metrics["confirmation_count"] == 1
    assert metrics["memory_candidate_count"] == 1
    assert feedback_response.status_code == 200
    assert candidates and candidates[0]["status"] == "pending_review"
    assert candidates[0]["artifact_template_json"]["run_id"] is None
    assert "confirmation_id" not in candidates[0]["artifact_template_json"]["actions"][0]
    assert approved_candidate["status"] == "approved"
    assert promoted_skill["name"] == approved_candidate["name"]
