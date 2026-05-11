from helpers import *  # noqa: F401,F403


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
