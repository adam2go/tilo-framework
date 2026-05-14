from helpers import *  # noqa: F401,F403


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

            assert result == {"artifacts": [], "confirmations": [], "memory_candidates": [], "surface_turns": []}
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
