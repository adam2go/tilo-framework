"""Tests for tilo.viewer (to_html, save_html) and custom skill loading."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tilo.viewer import to_html, save_html, _to_dict
from tilo.prompt import AIPPromptBuilder, BUILTIN_SKILLS, detect_skill
from tilo.schemas.artifact import ArtifactSpecV1


# --------------------------------------------------------------------------- #
# Fixtures                                                                     #
# --------------------------------------------------------------------------- #

def _rich_spec() -> dict:
    return {
        "version": "tilo/aip/v1",
        "title": "Test Surface",
        "status": "ready",
        "blocks": [
            {"id": "h", "type": "heading", "props": {"text": "Header", "severity": "high"}},
            {"id": "m1", "type": "metric", "props": {"label": "Score", "value": "8.2"}},
            {"id": "m2", "type": "metric", "props": {"label": "Count", "value": "24"}},
            {"id": "c", "type": "chart", "props": {"chart_type": "radar", "axes": [{"label": "A", "score": 5}, {"label": "B", "score": 8}]}},
            {"id": "tbl", "type": "table", "props": {"columns": [{"key": "x", "label": "X"}], "rows": [["1"], ["2"]]}},
            {"id": "d", "type": "diff", "props": {"before": "old", "after": "new"}},
            {"id": "cl", "type": "checklist", "props": {"items": [{"text": "Item 1", "checked": True}, {"text": "Item 2"}]}},
            {"id": "conf", "type": "confirmation", "props": {"description": "Approve?", "risk_level": "high"}},
            {"id": "mem", "type": "memory_card", "props": {"content": "Learned a preference", "confidence": 0.9}},
            {"id": "tl", "type": "timeline", "props": {"items": [{"time": "Day 1", "title": "Start"}]}},
        ],
        "views": [
            {"id": "v1", "label": "Main", "block_ids": ["h", "m1", "m2", "c", "tbl"]},
            {"id": "v2", "label": "Detail", "block_ids": ["d", "cl", "conf", "mem", "tl"]},
        ],
        "follow_ups": ["What next?", "Compare to baseline"],
    }


# --------------------------------------------------------------------------- #
# to_html                                                                      #
# --------------------------------------------------------------------------- #

class TestToHtml:
    def test_produces_valid_html(self):
        html = to_html(_rich_spec())
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html

    def test_title_in_output(self):
        html = to_html(_rich_spec())
        assert "Test Surface" in html

    def test_self_contained_no_cdn(self):
        html = to_html(_rich_spec())
        # No external script/style references
        assert "http://" not in html.split("<body>")[0] or "cdn" not in html.lower()
        assert "<script src=" not in html

    def test_includes_chart_js(self):
        html = to_html(_rich_spec())
        assert "renderChart" in html
        assert "renderRadar" in html

    def test_includes_render_js(self):
        html = to_html(_rich_spec())
        assert "renderBlock" in html
        assert "renderSpec" in html

    def test_spec_embedded_as_json(self):
        html = to_html(_rich_spec())
        assert "__tilo_spec__" in html

    def test_accepts_dict(self):
        html = to_html(_rich_spec())
        assert len(html) > 1000

    def test_accepts_json_string(self):
        html = to_html(json.dumps(_rich_spec()))
        assert "Test Surface" in html

    def test_accepts_pydantic_model(self):
        # Build a minimal valid ArtifactSpecV1
        spec = ArtifactSpecV1.model_validate({
            "version": "tilo/aip/v1",
            "title": "Model Spec",
            "status": "ready",
            "blocks": [{"id": "b", "type": "markdown", "props": {"content": "hi"}}],
            "views": [{"id": "v", "label": "V", "block_ids": ["b"]}],
        })
        html = to_html(spec)
        assert "Model Spec" in html

    def test_custom_title_override(self):
        html = to_html(_rich_spec(), title="Override Title")
        assert "Override Title" in html

    def test_follow_ups_present(self):
        html = to_html(_rich_spec())
        assert "What next?" in html


# --------------------------------------------------------------------------- #
# save_html                                                                    #
# --------------------------------------------------------------------------- #

class TestSaveHtml:
    def test_writes_file(self, tmp_path):
        out = tmp_path / "report.html"
        result = save_html(_rich_spec(), out)
        assert result.exists()
        assert result.read_text().startswith("<!DOCTYPE html>")

    def test_returns_resolved_path(self, tmp_path):
        out = tmp_path / "x.html"
        result = save_html(_rich_spec(), out)
        assert result.is_absolute()


# --------------------------------------------------------------------------- #
# _to_dict                                                                     #
# --------------------------------------------------------------------------- #

class TestToDict:
    def test_dict_passthrough(self):
        d = {"title": "x"}
        assert _to_dict(d) is d

    def test_json_string(self):
        assert _to_dict('{"title": "x"}') == {"title": "x"}

    def test_invalid_type_raises(self):
        with pytest.raises(TypeError):
            _to_dict(12345)


# --------------------------------------------------------------------------- #
# New built-in skills                                                          #
# --------------------------------------------------------------------------- #

class TestNewSkills:
    def test_twelve_skills_present(self):
        assert len(BUILTIN_SKILLS) == 12

    @pytest.mark.parametrize("key", [
        "incident_response", "meeting_summary", "bug_report",
        "document_review", "research_summary", "onboarding_plan",
    ])
    def test_new_skill_present(self, key):
        assert key in BUILTIN_SKILLS
        assert BUILTIN_SKILLS[key]["hints"].strip()

    def test_incident_detection(self):
        assert detect_skill("analyze this production incident outage") == "incident_response"
        assert detect_skill("write a post-mortem for the downtime") == "incident_response"

    def test_meeting_detection(self):
        assert detect_skill("summarize our standup meeting notes") == "meeting_summary"

    def test_bug_detection(self):
        assert detect_skill("debug this crash exception") == "bug_report"

    def test_onboarding_detection(self):
        assert detect_skill("onboarding plan for new developer") == "onboarding_plan"

    def test_research_detection(self):
        assert detect_skill("summarize this research paper") == "research_summary"

    def test_pr_word_boundary_not_matching_production(self):
        # Regression: "production" should NOT trigger code_review via " pr"
        assert detect_skill("the production incident") != "code_review"

    def test_pr_still_detected_as_word(self):
        assert detect_skill("review this PR") == "code_review"


# --------------------------------------------------------------------------- #
# Custom skill YAML loading                                                    #
# --------------------------------------------------------------------------- #

class TestCustomSkillLoading:
    def test_from_skill_file(self, tmp_path):
        skill_yaml = tmp_path / "skill.yaml"
        skill_yaml.write_text(
            "name: my-custom-skill\n"
            "block_hints:\n"
            "  - type: chart\n"
            "    variant: radar\n"
            "    use_when: \"Showing distribution\"\n"
            "  - type: timeline\n"
            "    use_when: \"Showing sequence\"\n"
            "view_hints: |\n"
            "  Organize into Overview and Detail tabs.\n"
        )
        builder = AIPPromptBuilder.from_skill_file("analyse my data", str(skill_yaml))
        user = builder.user_prompt()
        assert "chart(radar)" in user
        assert "Showing distribution" in user
        assert "Overview and Detail" in user

    def test_custom_hints_override_skill(self):
        builder = AIPPromptBuilder(
            "review contract",
            skill="contract_review",
            custom_hints="CUSTOM HINT TEXT HERE",
        )
        user = builder.user_prompt()
        assert "CUSTOM HINT TEXT HERE" in user

    def test_from_skill_file_real_contract_skill(self):
        # Load the actual repo skill file
        repo_root = Path(__file__).resolve().parents[2]
        skill_path = repo_root / "skills" / "contract-review" / "skill.yaml"
        if not skill_path.exists():
            pytest.skip("contract-review skill.yaml not found")
        builder = AIPPromptBuilder.from_skill_file("review my NDA", str(skill_path))
        user = builder.user_prompt()
        assert "radar" in user.lower() or "diff" in user.lower()


# --------------------------------------------------------------------------- #
# Playground & welcome routes                                                 #
# --------------------------------------------------------------------------- #

class TestPlaygroundRoutes:
    def _client(self):
        from fastapi.testclient import TestClient
        from tilo.main import app
        return TestClient(app)

    def test_welcome_page(self):
        r = self._client().get("/")
        assert r.status_code == 200
        assert "Tilo" in r.text
        assert "Playground" in r.text

    def test_playground_page(self):
        r = self._client().get("/playground")
        assert r.status_code == 200
        assert "Tilo Playground" in r.text
        assert "renderSpec" in r.text

    def test_playground_includes_skills(self):
        r = self._client().get("/playground")
        assert "contract_review" in r.text
        assert "incident_response" in r.text

    def test_health_still_works(self):
        r = self._client().get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
