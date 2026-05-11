from helpers import *  # noqa: F401,F403


def test_model_client_disabled_mode_is_explicit() -> None:
    client = ModelClient(Settings(llm_enabled=False, openai_api_key=""))

    assert client.enabled is False
    with pytest.raises(ModelDisabledError):
        client.chat_text_sync(system="system", user="user")
def test_model_client_resolves_mainstream_provider_presets() -> None:
    deepseek = ModelClient(Settings(llm_enabled=True, llm_provider="deepseek", deepseek_api_key="test-key"))
    anthropic = ModelClient(Settings(llm_enabled=True, llm_provider="anthropic", anthropic_api_key="test-key", default_model="claude-3-5-sonnet-latest"))
    tencent = ModelClient(Settings(llm_enabled=True, llm_provider="tencent", tencent_api_key="test-key", default_model="deepseek-v4-pro"))
    custom = ModelClient(Settings(llm_enabled=True, llm_provider="custom", llm_api_key="test-key", llm_base_url="https://models.example.com/v1"))

    assert deepseek.enabled is True
    assert deepseek.provider_family == "openai_compatible"
    assert deepseek.base_url == "https://api.deepseek.com"
    assert anthropic.enabled is True
    assert anthropic.provider_family == "anthropic"
    assert anthropic.base_url == "https://api.anthropic.com/v1"
    assert tencent.enabled is True
    assert tencent.provider_family == "openai_compatible"
    assert tencent.base_url == "https://tokenhub.tencentmaas.com/v1"
    assert custom.enabled is True
    assert custom.base_url == "https://models.example.com/v1"
def test_contract_review_llm_generator_falls_back_when_disabled() -> None:
    settings = Settings(llm_enabled=False, openai_api_key="")
    task = Task(workspace_id="workspace", title="Contract", input_message="Review payment and liability clauses.")
    result = ContractReviewLLMGenerator(settings).generate(task, [], [])

    assert result.status == "fallback"
    assert result.mode == "deterministic"
    assert result.data is None
    assert result.fallback_reason == "disabled"
def test_contract_review_llm_generator_falls_back_on_invalid_json() -> None:
    class InvalidJSONClient:
        enabled = True

        def chat_json_sync(self, **kwargs):
            raise ModelInvalidJSONError("invalid")

    settings = Settings(llm_enabled=True, openai_api_key="test-key")
    task = Task(workspace_id="workspace", title="Contract", input_message="Review payment and liability clauses.")
    result = ContractReviewLLMGenerator(settings, client=InvalidJSONClient()).generate(task, [], [])

    assert result.status == "fallback"
    assert result.mode == "deterministic"
    assert result.fallback_reason == "ModelInvalidJSONError"
def test_contract_review_llm_generator_prioritizes_liability_conflict_and_caps_full_review_findings() -> None:
    class VerboseClient:
        enabled = True

        def chat_json_sync(self, **kwargs):
            return {
                "risk_summary": {"high_count": 9, "medium_count": 9, "low_count": 9, "summary": "Review summary"},
                "risks": [
                    {"id": "risk_1", "clause": "Low", "risk_level": "low", "issue": "Low issue", "suggested_revision": "Low revision", "evidence": "Low evidence"},
                    {"id": "risk_2", "clause": "High A", "risk_level": "high", "issue": "High issue A", "suggested_revision": "High revision A", "evidence": "High evidence A"},
                    {"id": "risk_3", "clause": "Medium", "risk_level": "medium", "issue": "Medium issue", "suggested_revision": "Medium revision", "evidence": "Medium evidence"},
                    {"id": "risk_4", "clause": "High B", "risk_level": "high", "issue": "High issue B", "suggested_revision": "High revision B", "evidence": "High evidence B"},
                    {"id": "risk_5", "clause": "8.1 / 8.2", "risk_level": "high", "issue": "Liability cap and indemnity carve-outs conflict", "suggested_revision": "Narrow carve-outs", "evidence": "8.1 and 8.2"},
                    {"id": "risk_6", "clause": "Payment", "risk_level": "medium", "issue": "Payment issue", "suggested_revision": "Payment revision", "evidence": "Payment evidence"},
                    {"id": "risk_7", "clause": "SLA", "risk_level": "medium", "issue": "SLA issue", "suggested_revision": "SLA revision", "evidence": "SLA evidence"},
                    {"id": "risk_8", "clause": "IP", "risk_level": "medium", "issue": "IP issue", "suggested_revision": "IP revision", "evidence": "IP evidence"},
                    {"id": "risk_9", "clause": "Extra", "risk_level": "low", "issue": "Extra issue", "suggested_revision": "Extra revision", "evidence": "Extra evidence"},
                ],
                "revision_draft": {"heading": "Draft", "content": "Revision", "highlights": ["one", "two", "three", "four"]},
                "memory_candidate": {"type": "preference", "content": "Remember conservative review", "confidence": 0.8},
            }

    settings = Settings(llm_enabled=True, openai_api_key="test-key")
    task = Task(workspace_id="workspace", title="Contract", input_message="Review payment and liability clauses.")
    result = ContractReviewLLMGenerator(settings, client=VerboseClient()).generate(task, [], [])

    assert result.status == "success"
    assert result.data is not None
    assert result.data.risks[0].clause == "8.1 / 8.2"
    assert len(result.data.risks) == 8
    assert result.data.risk_summary.high_count == 3
    assert result.data.risk_summary.medium_count == 4
    assert result.data.risk_summary.low_count == 1
    assert len(result.data.revision_draft.highlights) == 3
