from helpers import *  # noqa: F401,F403


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
    assert any(event["event_type"] in ("candidate_created", "auto_confirmed") for event in write_events)
    assert tool_invocations and tool_invocations[0]["status"] == "completed"
    assert tool_invocations[0]["output_json"]["mock"] is True
    assert confirmations
    assert any(memory["status"] == "confirmed" and memory["is_confirmed"] is True for memory in memories)
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
        memories = client.get("/api/memories", params={"workspace_id": workspace_id, "status": "confirmed"}).json()
        reflection_memory = next(memory for memory in memories if memory.get("source_type") == "context_reflection")
        # Memory is already auto-confirmed; calling confirm again is a no-op but should not error.
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
    assert reflection_memory["is_confirmed"] is True
    assert reflection_memory["status"] == "confirmed"
    assert confirmed_memory["id"] == reflection_memory["id"]
    assert confirmed_memory["is_confirmed"] is True
    assert confirmed_memory["status"] == "confirmed"
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
