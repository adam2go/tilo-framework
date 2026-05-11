from helpers import *  # noqa: F401,F403


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
