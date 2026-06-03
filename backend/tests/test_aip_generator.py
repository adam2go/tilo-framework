"""Tests for the AIP spec generator and skill hint system."""
from helpers import *  # noqa: F401,F403

from tilo.services.artifact.aip_generator import (
    AIPSpecGenerator,
    ArtifactTypeDetector,
    _detect_skill_hint,
    _DEMO_SKILL_HINTS,
)


def test_skill_hint_detection_contract() -> None:
    hint = _detect_skill_hint("Review this contract for risky clauses")
    assert hint == _DEMO_SKILL_HINTS["contract_review"]


def test_skill_hint_detection_sales() -> None:
    hint = _detect_skill_hint("Follow up with my top customers")
    assert hint == _DEMO_SKILL_HINTS["sales_dashboard"]


def test_skill_hint_detection_code_review() -> None:
    hint = _detect_skill_hint("Review this pull request from the auth refactor branch")
    assert hint == _DEMO_SKILL_HINTS["code_review"]


def test_skill_hint_detection_generic() -> None:
    hint = _detect_skill_hint("Write me a poem about cats")
    assert hint is None


def test_artifact_type_detector() -> None:
    d = ArtifactTypeDetector()
    assert d.detect("review this contract") == "contract_review"
    assert d.detect("follow up with sales leads") == "dashboard"
    assert d.detect("review this pull request") == "code_review"
    assert d.detect("help me write a report") == "document"
    assert d.detect("审查这份合同") == "contract_review"
    assert d.detect("代码评审一下这个 PR") == "code_review"


def test_aip_deterministic_fallback() -> None:
    """AIPSpecGenerator without a model client should produce a valid deterministic spec."""
    task = Task(id="t1", workspace_id="ws", title="Test", input_message="Hello world")
    run = Run(id="r1", task_id="t1")
    gen = AIPSpecGenerator(client=None)
    result = gen.generate(task, run, [], [])
    assert result["version"] == "tilo/aip/v1"
    assert result["_generation_mode"] == "deterministic"
    assert len(result["blocks"]) >= 1
    spec = ArtifactSpecV1.model_validate(result)
    assert spec.title


def test_aip_deterministic_fallback_chinese() -> None:
    """Even with Chinese input, the demo fallback now returns English titles
    so the Canvas demo stays consistent. The hint detector still triggers
    contract scenario via Chinese keywords."""
    task = Task(id="t2", workspace_id="ws", title="Test", input_message="审查这份合同")
    run = Run(id="r2", task_id="t2")
    gen = AIPSpecGenerator(client=None)
    result = gen.generate(task, run, [], [])
    assert result["title"] == "Contract Review"
    assert len(result["blocks"]) >= 5  # Rich multi-block output
