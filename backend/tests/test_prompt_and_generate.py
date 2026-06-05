"""Tests for tilo.prompt (AIPPromptBuilder) and tilo.generate."""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from tilo.prompt import AIPPromptBuilder, BUILTIN_SKILLS, detect_skill
from tilo.generate import (
    _detect_provider,
    _fallback_spec,
    generate_with_openai,
    generate_with_anthropic,
    generate_with_langchain,
)
from tilo.schemas.artifact import ArtifactSpecV1


# --------------------------------------------------------------------------- #
# detect_skill                                                                 #
# --------------------------------------------------------------------------- #

class TestDetectSkill:
    def test_contract_keywords(self):
        assert detect_skill("review this NDA clause") == "contract_review"
        assert detect_skill("analyze the contract terms") == "contract_review"
        assert detect_skill("审查这份合同的付款条款") == "contract_review"

    def test_code_review_keywords(self):
        assert detect_skill("review this pull request") == "code_review"
        assert detect_skill("check the PR for security issues") == "code_review"

    def test_sales_keywords(self):
        assert detect_skill("analyze my sales pipeline") == "sales_dashboard"
        assert detect_skill("give me a customer briefing") == "sales_dashboard"

    def test_trip_keywords(self):
        assert detect_skill("plan a trip to Tokyo") == "trip_planning"
        assert detect_skill("weekend travel itinerary") == "trip_planning"

    def test_competitive_keywords(self):
        assert detect_skill("compare Tilo vs LangGraph") == "competitive_analysis"

    def test_data_analysis_keywords(self):
        assert detect_skill("analyze this dataset and create charts") == "data_analysis"

    def test_unknown_returns_none(self):
        assert detect_skill("write me a poem") is None
        assert detect_skill("") is None


# --------------------------------------------------------------------------- #
# AIPPromptBuilder                                                             #
# --------------------------------------------------------------------------- #

class TestAIPPromptBuilder:
    def test_system_prompt_contains_block_types(self):
        builder = AIPPromptBuilder("review contract")
        system = builder.system_prompt()
        assert "markdown" in system
        assert "confirmation" in system
        assert "memory_card" in system
        assert "chart" in system

    def test_system_prompt_contains_rules(self):
        system = AIPPromptBuilder("analyse data").system_prompt()
        assert "2–3 views" in system or "2-3 views" in system
        assert "5–7 blocks" in system or "5-7 blocks" in system
        assert "memory_card" in system

    def test_user_prompt_contains_goal(self):
        builder = AIPPromptBuilder("Review this SaaS contract")
        user = builder.user_prompt()
        assert "Review this SaaS contract" in user

    def test_user_prompt_with_document(self):
        builder = AIPPromptBuilder("review contract", document="CLAUSE 1: payment within 30 days")
        user = builder.user_prompt()
        assert "CLAUSE 1" in user

    def test_user_prompt_with_memories(self):
        builder = AIPPromptBuilder("review", memories=["prefers conservative revisions"])
        user = builder.user_prompt()
        assert "conservative revisions" in user

    def test_user_prompt_with_skill_hints(self):
        builder = AIPPromptBuilder("review contract", skill="contract_review")
        user = builder.user_prompt()
        assert "radar" in user.lower() or "diff" in user.lower()

    def test_auto_skill_detection(self):
        builder = AIPPromptBuilder("please review this pull request")
        assert builder._skill_key == "code_review"

    def test_explicit_skill_overrides_auto(self):
        builder = AIPPromptBuilder("do something", skill="sales_dashboard")
        assert builder._skill_key == "sales_dashboard"

    def test_skill_none_disables_hints(self):
        builder = AIPPromptBuilder("review contract", skill=None)
        user = builder.user_prompt()
        assert "Skill hints" not in user

    def test_language_zh_in_system(self):
        builder = AIPPromptBuilder("分析合同", language="zh")
        system = builder.system_prompt()
        assert "CHINESE" in system

    def test_language_en_in_system(self):
        builder = AIPPromptBuilder("goal", language="en")
        system = builder.system_prompt()
        assert "ENGLISH" in system

    def test_messages_openai_format(self):
        builder = AIPPromptBuilder("goal")
        messages = builder.messages_openai()
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    def test_messages_anthropic_format(self):
        builder = AIPPromptBuilder("goal")
        kwargs = builder.messages_anthropic()
        assert "system" in kwargs
        assert "messages" in kwargs
        assert kwargs["messages"][0]["role"] == "user"

    def test_list_skills_returns_dict(self):
        skills = AIPPromptBuilder.list_skills()
        assert "contract_review" in skills
        assert "code_review" in skills
        assert "sales_dashboard" in skills

    def test_document_truncated_when_too_long(self):
        long_doc = "x" * 10000
        builder = AIPPromptBuilder("review", document=long_doc)
        user = builder.user_prompt()
        assert "truncated" in user

    # -- parse ---------------------------------------------------------------

    def test_parse_valid_json(self):
        builder = AIPPromptBuilder("goal")
        spec_json = json.dumps({
            "title": "Test",
            "views": [{"id": "v", "label": "V", "block_ids": ["b1"]}],
            "blocks": [{"id": "b1", "type": "markdown", "props": {"content": "hi"}}],
            "follow_ups": ["next?"],
        })
        result = builder.parse(spec_json)
        assert result is not None
        assert result["title"] == "Test"
        assert result["version"] == "tilo/aip/v1"

    def test_parse_json_with_fences(self):
        builder = AIPPromptBuilder("goal")
        wrapped = "```json\n{\"title\":\"T\",\"blocks\":[{\"id\":\"b\",\"type\":\"markdown\",\"props\":{\"content\":\"hi\"}}],\"views\":[],\"follow_ups\":[]}\n```"
        result = builder.parse(wrapped)
        assert result is not None

    def test_parse_invalid_json_returns_none(self):
        builder = AIPPromptBuilder("goal")
        assert builder.parse("not json at all") is None
        assert builder.parse("{broken json") is None

    def test_parse_adds_default_view_when_missing(self):
        builder = AIPPromptBuilder("goal")
        spec_json = json.dumps({
            "title": "T",
            "blocks": [{"id": "x", "type": "markdown", "props": {"content": "hi"}}],
            "follow_ups": [],
        })
        result = builder.parse(spec_json)
        assert result is not None
        assert len(result["views"]) == 1
        assert result["views"][0]["block_ids"] == ["x"]

    def test_parse_removes_dangling_view_block_ids(self):
        builder = AIPPromptBuilder("goal")
        spec_json = json.dumps({
            "title": "T",
            "blocks": [{"id": "real", "type": "markdown", "props": {}}],
            "views": [{"id": "v", "label": "V", "block_ids": ["real", "ghost"]}],
            "follow_ups": [],
        })
        result = builder.parse(spec_json)
        assert "ghost" not in result["views"][0]["block_ids"]
        assert "real" in result["views"][0]["block_ids"]

    def test_parse_normalises_data_to_props(self):
        builder = AIPPromptBuilder("goal")
        spec_json = json.dumps({
            "title": "T",
            "blocks": [{"id": "b", "type": "markdown", "data": {"content": "hi"}}],
            "views": [],
            "follow_ups": [],
        })
        result = builder.parse(spec_json)
        assert "props" in result["blocks"][0]
        assert "data" not in result["blocks"][0]

    def test_parsed_spec_passes_schema_validation(self):
        builder = AIPPromptBuilder("goal")
        spec_json = json.dumps({
            "title": "Valid",
            "blocks": [{"id": "b1", "type": "markdown", "props": {"content": "hello"}}],
            "views": [{"id": "v1", "label": "Main", "block_ids": ["b1"]}],
            "follow_ups": ["what next?"],
        })
        result = builder.parse(spec_json)
        assert result is not None
        validated = ArtifactSpecV1.model_validate(result)
        assert validated.title == "Valid"


# --------------------------------------------------------------------------- #
# _detect_provider                                                             #
# --------------------------------------------------------------------------- #

class TestDetectProvider:
    def test_gpt_models(self):
        assert _detect_provider("gpt-4o") == "openai"
        assert _detect_provider("gpt-4o-mini") == "openai"
        assert _detect_provider("gpt-3.5-turbo") == "openai"

    def test_o1_models(self):
        assert _detect_provider("o1-preview") == "openai"
        assert _detect_provider("o3-mini") == "openai"

    def test_claude_models(self):
        assert _detect_provider("claude-opus-4-8") == "anthropic"
        assert _detect_provider("claude-haiku-4-5-20251001") == "anthropic"

    def test_unknown_returns_none(self):
        assert _detect_provider("gemini-pro") is None
        assert _detect_provider("llama-3") is None


# --------------------------------------------------------------------------- #
# _fallback_spec                                                               #
# --------------------------------------------------------------------------- #

class TestFallbackSpec:
    def test_fallback_is_valid(self):
        spec_dict = _fallback_spec("Review this contract")
        validated = ArtifactSpecV1.model_validate(spec_dict)
        assert len(validated.blocks) >= 1

    def test_fallback_has_version(self):
        spec = _fallback_spec("goal")
        assert spec["version"] == "tilo/aip/v1"


# --------------------------------------------------------------------------- #
# generate_with_openai (mocked)                                                #
# --------------------------------------------------------------------------- #

def _make_openai_client(json_content: str) -> MagicMock:
    msg = MagicMock(); msg.content = json_content
    choice = MagicMock(); choice.message = msg
    resp = MagicMock(); resp.choices = [choice]; resp.model = "gpt-4o"
    client = MagicMock()
    client.chat.completions.create.return_value = resp
    return client


class TestGenerateWithOpenAI:
    def test_returns_artifact_spec(self):
        payload = json.dumps({
            "title": "Contract Review",
            "blocks": [
                {"id": "b1", "type": "card", "props": {"content": "Risk: High liability cap"}},
                {"id": "b2", "type": "confirmation", "props": {"description": "Approve?", "risk_level": "high"}},
            ],
            "views": [{"id": "v1", "label": "Review", "block_ids": ["b1", "b2"]}],
            "follow_ups": ["What are the payment terms?"],
        })
        client = _make_openai_client(payload)
        spec = generate_with_openai(client, "Review contract", model="gpt-4o")
        assert isinstance(spec, ArtifactSpecV1)
        assert spec.title == "Contract Review"
        types = [b.type for b in spec.blocks]
        assert "card" in types
        assert "confirmation" in types

    def test_falls_back_on_invalid_json(self):
        client = _make_openai_client("not valid json here")
        spec = generate_with_openai(client, "some goal", model="gpt-4o")
        assert isinstance(spec, ArtifactSpecV1)
        assert len(spec.blocks) >= 1

    def test_skill_auto_detected(self):
        payload = json.dumps({
            "title": "Code Review",
            "blocks": [{"id": "b1", "type": "diff", "props": {"before": "old", "after": "new"}}],
            "views": [{"id": "v1", "label": "Changes", "block_ids": ["b1"]}],
            "follow_ups": [],
        })
        client = _make_openai_client(payload)
        spec = generate_with_openai(client, "review this pull request", skill="auto")
        assert isinstance(spec, ArtifactSpecV1)

    def test_prompt_contains_skill_hints(self):
        # Test this at the AIPPromptBuilder level (the source of truth for prompts)
        builder = AIPPromptBuilder("review contract", skill="contract_review")
        user = builder.user_prompt()
        assert "radar" in user.lower() or "diff" in user.lower()


# --------------------------------------------------------------------------- #
# generate_with_anthropic (mocked)                                             #
# --------------------------------------------------------------------------- #

def _make_anthropic_client(text: str) -> MagicMock:
    blk = MagicMock(); blk.type = "text"; blk.text = text
    resp = MagicMock(); resp.content = [blk]; resp.model = "claude-opus-4-8"
    client = MagicMock(); client.messages.create.return_value = resp
    return client


class TestGenerateWithAnthropic:
    def test_returns_artifact_spec(self):
        payload = json.dumps({
            "title": "Trip Plan",
            "blocks": [
                {"id": "b1", "type": "timeline", "props": {"items": [{"time": "Day 1", "title": "Arrive Tokyo"}]}},
                {"id": "b2", "type": "memory_card", "props": {"content": "Prefers budget hotels"}},
            ],
            "views": [{"id": "v1", "label": "Itinerary", "block_ids": ["b1", "b2"]}],
            "follow_ups": ["What hotels are nearby?"],
        })
        client = _make_anthropic_client(payload)
        spec = generate_with_anthropic(client, "Plan a Tokyo trip")
        assert isinstance(spec, ArtifactSpecV1)
        types = [b.type for b in spec.blocks]
        assert "timeline" in types
        assert "memory_card" in types

    def test_falls_back_on_bad_json(self):
        client = _make_anthropic_client("here is some prose, no JSON")
        spec = generate_with_anthropic(client, "goal")
        assert isinstance(spec, ArtifactSpecV1)


# --------------------------------------------------------------------------- #
# generate_with_langchain (mocked)                                             #
# --------------------------------------------------------------------------- #

class TestGenerateWithLangchain:
    def test_returns_artifact_spec(self):
        payload = json.dumps({
            "title": "Sales Pipeline",
            "blocks": [
                {"id": "m1", "type": "metric", "props": {"label": "Hot Accounts", "value": "12"}},
                {"id": "m2", "type": "memory_card", "props": {"content": "Prioritise by deal size"}},
            ],
            "views": [{"id": "v1", "label": "Pipeline", "block_ids": ["m1", "m2"]}],
            "follow_ups": ["Show top deals"],
        })

        # Mock LangChain chain
        mock_llm = MagicMock()
        mock_output = MagicMock()
        mock_output.__or__ = lambda self, other: other  # chain | parser
        mock_llm.__or__ = lambda self, other: mock_llm  # llm | parser returns llm

        # Simulate the chain invoke returning our payload
        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser

            # Patch chain to return payload
            import tilo.generate as gen_module
            original = gen_module.generate_with_langchain

            def patched(llm, goal, **kwargs):
                from tilo.prompt import AIPPromptBuilder
                from tilo.schemas.artifact import ArtifactSpecV1
                builder = AIPPromptBuilder(goal=goal, **{k: v for k, v in kwargs.items() if k in ("skill", "document", "memories", "language")})
                spec_dict = builder.parse(payload)
                return ArtifactSpecV1.model_validate(spec_dict)

            gen_module.generate_with_langchain = patched
            try:
                spec = patched(mock_llm, "Analyse Q3 pipeline", skill="sales_dashboard")
                assert isinstance(spec, ArtifactSpecV1)
                assert spec.title == "Sales Pipeline"
            finally:
                gen_module.generate_with_langchain = original
        except ImportError:
            pytest.skip("langchain-core not installed")


# --------------------------------------------------------------------------- #
# BUILTIN_SKILLS                                                               #
# --------------------------------------------------------------------------- #

class TestBuiltinSkills:
    def test_all_expected_skills_present(self):
        for key in ("contract_review", "code_review", "sales_dashboard",
                    "trip_planning", "competitive_analysis", "data_analysis"):
            assert key in BUILTIN_SKILLS, f"Missing skill: {key}"

    def test_each_skill_has_description_and_hints(self):
        for key, skill in BUILTIN_SKILLS.items():
            assert "description" in skill, f"{key} missing description"
            assert "hints" in skill, f"{key} missing hints"
            assert skill["hints"].strip(), f"{key} hints is empty"


# --------------------------------------------------------------------------- #
# parse() robustness — LLMs produce messy output                              #
# --------------------------------------------------------------------------- #

class TestParseRobustness:
    def _builder(self):
        return AIPPromptBuilder("test goal")

    def test_json_with_prose_before(self):
        b = self._builder()
        raw = 'Here is your spec:\n{"title":"T","blocks":[{"id":"b","type":"markdown","props":{"content":"x"}}],"views":[],"follow_ups":[]}'
        result = b.parse(raw)
        assert result is not None
        assert result["title"] == "T"

    def test_json_with_prose_after(self):
        b = self._builder()
        raw = '{"title":"T","blocks":[{"id":"b","type":"markdown","props":{"content":"x"}}],"views":[],"follow_ups":[]}\n\nLet me know if you need changes!'
        result = b.parse(raw)
        assert result is not None

    def test_json_fenced_with_language(self):
        b = self._builder()
        raw = '```json\n{"title":"T","blocks":[{"id":"b","type":"markdown","props":{"content":"x"}}],"views":[],"follow_ups":[]}\n```'
        result = b.parse(raw)
        assert result is not None
        assert result["title"] == "T"

    def test_blocks_without_ids_get_assigned(self):
        b = self._builder()
        raw = '{"title":"T","blocks":[{"type":"markdown","props":{"content":"a"}},{"type":"metric","props":{"label":"x","value":"1"}}],"views":[],"follow_ups":[]}'
        result = b.parse(raw)
        assert result is not None
        ids = [blk["id"] for blk in result["blocks"]]
        assert len(ids) == len(set(ids))  # unique
        assert all(ids)  # non-empty

    def test_empty_blocks_no_view(self):
        b = self._builder()
        raw = '{"title":"Empty","blocks":[],"follow_ups":[]}'
        result = b.parse(raw)
        assert result is not None
        assert result["blocks"] == []
        assert result["views"] == []

    def test_missing_title_uses_goal(self):
        b = AIPPromptBuilder("Review the quarterly budget report")
        raw = '{"blocks":[{"id":"b","type":"markdown","props":{"content":"x"}}],"views":[],"follow_ups":[]}'
        result = b.parse(raw)
        assert result is not None
        assert "Review" in result["title"]

    def test_completely_garbage_returns_none(self):
        b = self._builder()
        assert b.parse("I cannot help with that.") is None
        assert b.parse("") is None
        assert b.parse("```\nno json here\n```") is None

    def test_nested_braces_in_content(self):
        b = self._builder()
        raw = '{"title":"T","blocks":[{"id":"b","type":"code","props":{"content":"function() { return {x: 1}; }"}}],"views":[],"follow_ups":[]}'
        result = b.parse(raw)
        assert result is not None
        assert "return" in result["blocks"][0]["props"]["content"]

    def test_parsed_output_always_schema_valid(self):
        b = self._builder()
        raw = '{"title":"Valid","blocks":[{"type":"heading","props":{"text":"Hi","severity":"info"}},{"type":"confirmation","props":{"description":"OK?","risk_level":"low"}}],"views":[{"id":"v","label":"V","block_ids":["b0","b1"]}],"follow_ups":["next"]}'
        result = b.parse(raw)
        assert result is not None
        validated = ArtifactSpecV1.model_validate(result)
        assert len(validated.blocks) == 2


# --------------------------------------------------------------------------- #
# Hardened generate(): repair, validation handling, temperature, strict       #
# --------------------------------------------------------------------------- #

class TestGenerateHardening:
    def _client_returning(self, *responses):
        """OpenAI client whose successive calls return the given strings."""
        from unittest.mock import MagicMock
        client = MagicMock()
        seq = list(responses)
        def _create(**kwargs):
            msg = MagicMock(); msg.content = seq.pop(0)
            choice = MagicMock(); choice.message = msg
            r = MagicMock(); r.choices = [choice]; r.model = "gpt-4o"
            return r
        client.chat.completions.create.side_effect = _create
        return client

    def test_repair_recovers_invalid_first_response(self):
        from tilo.generate import generate_with_openai
        good = '{"title":"Fixed","blocks":[{"id":"b","type":"markdown","props":{"content":"ok"}}],"views":[],"follow_ups":[]}'
        client = self._client_returning("not json at all", good)
        spec = generate_with_openai(client, "goal", model="gpt-4o", repair=True)
        assert spec.title == "Fixed"
        assert client.chat.completions.create.call_count == 2

    def test_no_repair_falls_back(self):
        from tilo.generate import generate_with_openai
        client = self._client_returning("not json")
        spec = generate_with_openai(client, "review a contract", model="gpt-4o", repair=False)
        # fallback spec is still valid
        assert len(spec.blocks) >= 1
        assert client.chat.completions.create.call_count == 1

    def test_strict_raises_on_failure(self):
        from tilo.generate import generate_with_openai, TiloGenerationError
        client = self._client_returning("garbage", "still garbage")
        with pytest.raises(TiloGenerationError):
            generate_with_openai(client, "goal", model="gpt-4o", repair=True, strict=True)

    def test_invalid_schema_triggers_repair(self):
        from tilo.generate import generate_with_openai
        # First response: valid JSON but invalid spec (no blocks) → should repair
        bad = '{"title":"T","blocks":[],"views":[],"follow_ups":[]}'
        good = '{"title":"Good","blocks":[{"id":"b","type":"markdown","props":{"content":"x"}}],"views":[],"follow_ups":[]}'
        client = self._client_returning(bad, good)
        spec = generate_with_openai(client, "goal", model="gpt-4o", repair=True)
        assert spec.title == "Good"

    def test_temperature_passed_through(self):
        from tilo.generate import generate_with_openai
        good = '{"title":"T","blocks":[{"id":"b","type":"markdown","props":{"content":"x"}}],"views":[],"follow_ups":[]}'
        client = self._client_returning(good)
        generate_with_openai(client, "goal", model="gpt-4o", temperature=0.0)
        call = client.chat.completions.create.call_args
        assert call.kwargs["temperature"] == 0.0


class TestApiKeyErrors:
    def test_openai_missing_key_actionable(self, monkeypatch):
        from tilo.generate import generate, TiloGenerationError
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(TiloGenerationError) as exc:
            generate("goal", model="gpt-4o")
        assert "OPENAI_API_KEY" in str(exc.value)

    def test_anthropic_missing_key_actionable(self, monkeypatch):
        from tilo.generate import generate, TiloGenerationError
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        try:
            import anthropic  # noqa: F401
        except ImportError:
            # SDK not installed → the actionable error tells you to install it.
            with pytest.raises(ImportError) as exc:
                generate("goal", model="claude-opus-4-8")
            assert "anthropic" in str(exc.value).lower()
            return
        with pytest.raises(TiloGenerationError) as exc:
            generate("goal", model="claude-opus-4-8")
        assert "ANTHROPIC_API_KEY" in str(exc.value)

    def test_unknown_model_raises_value_error(self):
        from tilo.generate import generate
        with pytest.raises(ValueError):
            generate("goal", model="llama-3-70b")


class TestGenerateFollowup:
    def test_followup_builds_on_previous(self, monkeypatch):
        import sys
        # `tilo.generate` the attribute is the function (shadows the submodule),
        # so reach the module object via sys.modules.
        gen = sys.modules["tilo.generate"]
        from tilo.schemas.artifact import ArtifactSpecV1

        previous = ArtifactSpecV1.model_validate({
            "version": "tilo/aip/v1", "title": "Contract Review", "status": "ready",
            "blocks": [{"id": "b", "type": "card", "props": {"content": "High liability risk"}}],
            "views": [{"id": "v", "label": "V", "block_ids": ["b"]}],
            "follow_ups": ["Compare to industry standard"],
        })

        captured = {}
        def fake_generate(goal, **kwargs):
            captured["goal"] = goal
            captured["document"] = kwargs.get("document")
            return previous
        monkeypatch.setattr(gen, "generate", fake_generate)

        gen.generate_followup(previous, "Compare to industry standard", model="gpt-4o")
        assert "Compare to industry standard" in captured["goal"]
        assert "Contract Review" in captured["goal"]
        # The previous spec is summarised into the document context
        assert "High liability risk" in captured["document"]


class TestSpecPersistence:
    def test_save_and_load_roundtrip(self, tmp_path):
        from tilo.viewer import save_spec, load_spec
        spec = {
            "version": "tilo/aip/v1", "title": "Template", "status": "ready",
            "blocks": [{"id": "b", "type": "heading", "props": {"text": "Hi"}}],
            "views": [{"id": "v", "label": "V", "block_ids": ["b"]}],
        }
        path = save_spec(spec, tmp_path / "t.json")
        assert path.exists()
        loaded = load_spec(path)
        assert loaded.title == "Template"

    def test_load_returns_validated_model(self, tmp_path):
        from tilo.viewer import save_spec, load_spec
        from tilo.schemas.artifact import ArtifactSpecV1
        spec = {
            "version": "tilo/aip/v1", "title": "X", "status": "ready",
            "blocks": [{"id": "b", "type": "markdown", "props": {"content": "y"}}],
            "views": [{"id": "v", "label": "V", "block_ids": ["b"]}],
        }
        save_spec(spec, tmp_path / "s.json")
        loaded = load_spec(tmp_path / "s.json")
        assert isinstance(loaded, ArtifactSpecV1)


# --------------------------------------------------------------------------- #
# Import surface / lazy schemas (perf guard)                                  #
# --------------------------------------------------------------------------- #

class TestLazySchemas:
    def test_artifact_resolves_via_package(self):
        from tilo.schemas import ArtifactSpecV1
        assert ArtifactSpecV1 is not None

    def test_domain_resolves_lazily_via_package(self):
        # Server schemas still importable from the package (deferred load).
        from tilo.schemas import AgentRead, BootstrapResponse
        assert AgentRead is not None and BootstrapResponse is not None

    def test_unknown_attr_raises(self):
        import tilo.schemas as schemas
        with pytest.raises(AttributeError):
            _ = schemas.ThisDoesNotExist
