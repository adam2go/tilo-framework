from helpers import *  # noqa: F401,F403


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
