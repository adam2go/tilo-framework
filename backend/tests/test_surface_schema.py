"""Tests for the Tilo Surface Protocol v1 (Phase 0).

These tests are the executable contract for the protocol.
They cover:

1. Round-trip parsing for one valid example per intent.
2. The 10 normative validation rules (§7 of docs/SURFACE_PROTOCOL.md).
3. Cross-block action_id reference validation.
4. Block.data shape validation per type.
5. JSON Schema export stays in sync (smoke check; full check via the script).
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tilo.schemas.surface import (
    NOOP_ACTION_ID,
    SURFACE_SCHEMA_VERSION,
    SurfaceBlock,
    SurfaceBlockType,
    SurfaceIntent,
    SurfaceSpecV1,
)


# --------------------------------------------------------------------------- #
# Reusable fixtures                                                           #
# --------------------------------------------------------------------------- #


def _decision_block() -> dict:
    return {
        "id": "blk_decision",
        "type": "decision",
        "data": {
            "prompt": "How should I proceed?",
            "mode": "single",
            "options": [
                {"id": "o1", "label": "Approve", "value": "approve", "action_id": "approve_revision"},
                {"id": "o2", "label": "Reject", "value": "reject", "action_id": "reject_revision"},
            ],
        },
        "fallback_text": "Reply approve or reject.",
        "actions": [
            {
                "id": "approve_revision",
                "label": "Approve",
                "action_type": "approve",
                "confirmation_required": True,
                "payload": {"operation": "approve_revision"},
            },
            {
                "id": "reject_revision",
                "label": "Reject",
                "action_type": "reject",
                "confirmation_required": False,
                "payload": {},
            },
        ],
    }


def _minimal_spec(**overrides) -> dict:
    spec = {
        "schema_version": SURFACE_SCHEMA_VERSION,
        "surface_id": "srf_test",
        "turn_id": "trn_test",
        "run_id": "run_test",
        "intent": "request_approval",
        "budget_hint": "mini",
        "block_compat": "graceful",
        "blocks": [_decision_block()],
        "fallback_text": "Approve or reject?",
    }
    spec.update(overrides)
    return spec


# --------------------------------------------------------------------------- #
# 1. Round-trip parsing for one valid example per intent                      #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "intent,blocks",
    [
        (
            SurfaceIntent.request_approval,
            [
                {
                    "id": "h",
                    "type": "heading",
                    "data": {"text": "Liability cap unusually low", "severity": "high"},
                    "fallback_text": "Liability cap unusually low.",
                },
                _decision_block(),
            ],
        ),
        (
            SurfaceIntent.collect_input,
            [
                {
                    "id": "h",
                    "type": "heading",
                    "data": {"text": "What cap should we counter with?"},
                    "fallback_text": "What cap to counter with?",
                },
                {
                    "id": "f",
                    "type": "form",
                    "data": {
                        "fields": [
                            {"name": "cap_months", "label": "Cap (months)", "kind": "number", "required": True, "min": 1, "max": 36},
                        ],
                        "submit_action_id": "submit_cap",
                    },
                    "fallback_text": "Reply with the requested cap in months.",
                    "actions": [
                        {
                            "id": "submit_cap",
                            "label": "Submit",
                            "action_type": "continue_task",
                            "confirmation_required": False,
                            "payload": {},
                        }
                    ],
                },
            ],
        ),
        (
            SurfaceIntent.present_result,
            [
                {
                    "id": "h",
                    "type": "heading",
                    "data": {"text": "Review complete"},
                    "fallback_text": "Review complete.",
                },
                {
                    "id": "l",
                    "type": "list",
                    "data": {
                        "ordered": False,
                        "items": [
                            {"text": "Liability cap: 3 months", "severity": "high"},
                            {"text": "Termination notice: 90 days", "severity": "medium"},
                        ],
                    },
                    "fallback_text": "Two findings: liability cap, termination notice.",
                },
            ],
        ),
        (
            SurfaceIntent.offer_choices,
            [
                {
                    "id": "h",
                    "type": "heading",
                    "data": {"text": "Pick a tone"},
                    "fallback_text": "Pick a tone.",
                },
                {
                    "id": "d",
                    "type": "decision",
                    "data": {
                        "mode": "single",
                        "options": [
                            {"id": "o1", "label": "Conservative", "value": "conservative", "action_id": "pick"},
                            {"id": "o2", "label": "Aggressive", "value": "aggressive", "action_id": "pick"},
                        ],
                    },
                    "fallback_text": "Reply conservative or aggressive.",
                    "actions": [
                        {"id": "pick", "label": "Pick", "action_type": "select", "confirmation_required": False, "payload": {}}
                    ],
                },
            ],
        ),
        (
            SurfaceIntent.confirm_memory,
            [
                {
                    "id": "h",
                    "type": "heading",
                    "data": {"text": "Should I remember this?"},
                    "fallback_text": "Remember this preference?",
                },
                {
                    "id": "t",
                    "type": "text",
                    "data": {"content": "User prefers liability caps >= 12 months ARR."},
                    "fallback_text": "Preference: liability cap >= 12 months ARR.",
                },
                {
                    "id": "d",
                    "type": "decision",
                    "data": {
                        "mode": "single",
                        "options": [
                            {"id": "o1", "label": "Yes", "value": "confirm", "action_id": "make_memory"},
                            {"id": "o2", "label": "No", "value": "reject", "action_id": "drop"},
                        ],
                    },
                    "fallback_text": "Reply yes or no.",
                    "actions": [
                        {"id": "make_memory", "label": "Yes", "action_type": "create_memory", "confirmation_required": False, "payload": {"content": "User prefers caps >= 12mo"}},
                        {"id": "drop", "label": "No", "action_type": "reject", "confirmation_required": False, "payload": {}},
                    ],
                },
            ],
        ),
        (
            SurfaceIntent.show_progress,
            [
                {
                    "id": "h",
                    "type": "heading",
                    "data": {"text": "Reviewing contract..."},
                    "fallback_text": "Reviewing.",
                },
                {
                    "id": "p",
                    "type": "progress",
                    "data": {
                        "shape": "steps",
                        "steps": [
                            {"id": "s1", "label": "Recall memory", "state": "done"},
                            {"id": "s2", "label": "Score risks", "state": "running"},
                            {"id": "s3", "label": "Draft revision", "state": "pending"},
                        ],
                    },
                    "fallback_text": "Step 2 of 3 in progress.",
                },
            ],
        ),
        (
            SurfaceIntent.escalate_to_rich,
            [
                {
                    "id": "h",
                    "type": "heading",
                    "data": {"text": "Full review available"},
                    "fallback_text": "Full review available.",
                },
                {
                    "id": "al",
                    "type": "artifact_link",
                    "data": {
                        "artifact_id": "art_1",
                        "title": "Contract Review v3",
                        "summary": "12 risks (4 high)",
                        "open_action_id": "open",
                    },
                    "fallback_text": "Open the full review.",
                    "actions": [
                        {"id": "open", "label": "Open", "action_type": "select", "confirmation_required": False, "payload": {"operation": "open_rich"}}
                    ],
                },
            ],
        ),
        (
            SurfaceIntent.ask_clarification,
            [
                {
                    "id": "h",
                    "type": "heading",
                    "data": {"text": "Could you clarify?"},
                    "fallback_text": "Could you clarify?",
                },
                {
                    "id": "t",
                    "type": "text",
                    "data": {"content": "Should liability cap apply to both parties?"},
                    "fallback_text": "Should liability cap apply to both parties?",
                },
            ],
        ),
    ],
)
def test_round_trip_per_intent(intent: SurfaceIntent, blocks: list[dict]) -> None:
    raw = _minimal_spec(intent=intent.value, blocks=blocks)
    # Adjust budget_hint: rich for escalate_to_rich, mini otherwise.
    raw["budget_hint"] = "rich" if intent == SurfaceIntent.escalate_to_rich else "mini"

    spec = SurfaceSpecV1.model_validate(raw)
    assert spec.intent == intent
    # Round-trip through JSON.
    dumped = json.loads(spec.model_dump_json())
    assert dumped["schema_version"] == SURFACE_SCHEMA_VERSION
    assert dumped["intent"] == intent.value
    assert len(dumped["blocks"]) == len(blocks)


# --------------------------------------------------------------------------- #
# 2. Top-level validation rules                                               #
# --------------------------------------------------------------------------- #


def test_rule_1_schema_version_must_match() -> None:
    raw = _minimal_spec(schema_version="tilo.surface.v0")
    with pytest.raises(ValidationError):
        SurfaceSpecV1.model_validate(raw)


def test_rule_2_intent_must_be_in_vocab() -> None:
    raw = _minimal_spec(intent="invent_new_intent")
    with pytest.raises(ValidationError):
        SurfaceSpecV1.model_validate(raw)


def test_rule_3_blocks_must_be_non_empty() -> None:
    raw = _minimal_spec(blocks=[])
    with pytest.raises(ValidationError):
        SurfaceSpecV1.model_validate(raw)


def test_rule_4_block_type_must_be_in_vocab() -> None:
    raw = _minimal_spec(blocks=[{
        "id": "x",
        "type": "carousel",
        "data": {},
        "fallback_text": "x",
    }])
    with pytest.raises(ValidationError):
        SurfaceSpecV1.model_validate(raw)


def test_rule_6_fallback_text_required() -> None:
    bad_top = _minimal_spec(fallback_text="")
    with pytest.raises(ValidationError):
        SurfaceSpecV1.model_validate(bad_top)

    bad_block = _minimal_spec()
    bad_block["blocks"][0]["fallback_text"] = ""
    with pytest.raises(ValidationError):
        SurfaceSpecV1.model_validate(bad_block)


def test_rule_9_budget_hint_enum() -> None:
    with pytest.raises(ValidationError):
        SurfaceSpecV1.model_validate(_minimal_spec(budget_hint="huge"))


def test_rule_10_block_compat_enum() -> None:
    with pytest.raises(ValidationError):
        SurfaceSpecV1.model_validate(_minimal_spec(block_compat="lenient"))


# --------------------------------------------------------------------------- #
# 3. Cross-block action_id reference validation (rules 7-8)                   #
# --------------------------------------------------------------------------- #


def test_decision_option_action_id_must_exist_in_block_actions() -> None:
    block = _decision_block()
    block["data"]["options"][0]["action_id"] = "does_not_exist"
    raw = _minimal_spec(blocks=[block])
    with pytest.raises(ValidationError) as exc:
        SurfaceSpecV1.model_validate(raw)
    assert "does_not_exist" in str(exc.value)


def test_noop_action_id_is_allowed() -> None:
    block = _decision_block()
    block["data"]["options"].append(
        {"id": "o3", "label": "Cancel", "value": "cancel", "action_id": NOOP_ACTION_ID}
    )
    raw = _minimal_spec(blocks=[block])
    SurfaceSpecV1.model_validate(raw)  # must not raise


def test_form_submit_action_id_must_exist() -> None:
    raw = _minimal_spec(blocks=[
        {
            "id": "f",
            "type": "form",
            "data": {
                "fields": [{"name": "x", "label": "X", "kind": "text", "required": True}],
                "submit_action_id": "missing_action",
            },
            "fallback_text": "Fill the form.",
            "actions": [],
        }
    ])
    with pytest.raises(ValidationError) as exc:
        SurfaceSpecV1.model_validate(raw)
    assert "missing_action" in str(exc.value)


def test_artifact_link_open_action_id_must_exist() -> None:
    raw = _minimal_spec(
        intent="escalate_to_rich",
        budget_hint="rich",
        blocks=[
            {
                "id": "al",
                "type": "artifact_link",
                "data": {
                    "artifact_id": "a",
                    "title": "T",
                    "open_action_id": "missing",
                },
                "fallback_text": "Open it.",
                "actions": [],
            }
        ],
    )
    with pytest.raises(ValidationError) as exc:
        SurfaceSpecV1.model_validate(raw)
    assert "missing" in str(exc.value)


def test_duplicate_block_ids_rejected() -> None:
    block_a = _decision_block()
    block_b = copy.deepcopy(block_a)
    raw = _minimal_spec(blocks=[block_a, block_b])
    with pytest.raises(ValidationError) as exc:
        SurfaceSpecV1.model_validate(raw)
    assert "Duplicate block id" in str(exc.value)


# --------------------------------------------------------------------------- #
# 4. Per-block data shape validation                                          #
# --------------------------------------------------------------------------- #


def test_heading_requires_text() -> None:
    raw = _minimal_spec(blocks=[
        {"id": "h", "type": "heading", "data": {}, "fallback_text": "x"}
    ])
    with pytest.raises(ValidationError):
        SurfaceSpecV1.model_validate(raw)


def test_comparison_side_by_side_requires_left_right() -> None:
    raw = _minimal_spec(blocks=[
        {
            "id": "c",
            "type": "comparison",
            "data": {"shape": "side_by_side"},
            "fallback_text": "x",
        }
    ])
    with pytest.raises(ValidationError) as exc:
        SurfaceSpecV1.model_validate(raw)
    assert "side_by_side" in str(exc.value)


def test_comparison_table_requires_rows() -> None:
    raw = _minimal_spec(blocks=[
        {
            "id": "c",
            "type": "comparison",
            "data": {"shape": "table"},
            "fallback_text": "x",
        }
    ])
    with pytest.raises(ValidationError):
        SurfaceSpecV1.model_validate(raw)


def test_form_select_requires_options() -> None:
    raw = _minimal_spec(blocks=[
        {
            "id": "f",
            "type": "form",
            "data": {
                "fields": [{"name": "x", "label": "X", "kind": "select"}],
                "submit_action_id": "submit",
            },
            "fallback_text": "x",
            "actions": [
                {"id": "submit", "label": "Submit", "action_type": "continue_task", "confirmation_required": False, "payload": {}}
            ],
        }
    ])
    with pytest.raises(ValidationError) as exc:
        SurfaceSpecV1.model_validate(raw)
    assert "options" in str(exc.value)


def test_form_min_max_only_on_number() -> None:
    raw = _minimal_spec(blocks=[
        {
            "id": "f",
            "type": "form",
            "data": {
                "fields": [{"name": "x", "label": "X", "kind": "text", "min": 1}],
                "submit_action_id": "submit",
            },
            "fallback_text": "x",
            "actions": [
                {"id": "submit", "label": "Submit", "action_type": "continue_task", "confirmation_required": False, "payload": {}}
            ],
        }
    ])
    with pytest.raises(ValidationError):
        SurfaceSpecV1.model_validate(raw)


def test_progress_steps_shape_requires_steps() -> None:
    raw = _minimal_spec(blocks=[
        {"id": "p", "type": "progress", "data": {"shape": "steps"}, "fallback_text": "x"}
    ])
    with pytest.raises(ValidationError):
        SurfaceSpecV1.model_validate(raw)


def test_progress_percent_shape_requires_percent() -> None:
    raw = _minimal_spec(blocks=[
        {"id": "p", "type": "progress", "data": {"shape": "percent"}, "fallback_text": "x"}
    ])
    with pytest.raises(ValidationError):
        SurfaceSpecV1.model_validate(raw)


def test_editable_structured_requires_schema() -> None:
    raw = _minimal_spec(blocks=[
        {
            "id": "e",
            "type": "editable",
            "data": {
                "kind": "structured",
                "value": "{}",
                "submit_action_id": "save",
            },
            "fallback_text": "x",
            "actions": [
                {"id": "save", "label": "Save", "action_type": "edit", "confirmation_required": False, "payload": {}}
            ],
        }
    ])
    with pytest.raises(ValidationError) as exc:
        SurfaceSpecV1.model_validate(raw)
    assert "schema" in str(exc.value)


def test_unknown_field_in_block_data_rejected() -> None:
    raw = _minimal_spec(blocks=[
        {
            "id": "h",
            "type": "heading",
            "data": {"text": "Hi", "color": "red"},  # color not in schema
            "fallback_text": "Hi.",
        }
    ])
    with pytest.raises(ValidationError):
        SurfaceSpecV1.model_validate(raw)


# --------------------------------------------------------------------------- #
# 5. Action type vocabulary remains the existing closed set                   #
# --------------------------------------------------------------------------- #


def test_unsupported_action_type_rejected() -> None:
    block = _decision_block()
    block["actions"][0]["action_type"] = "broadcast"  # not in supported set
    raw = _minimal_spec(blocks=[block])
    with pytest.raises(ValidationError):
        SurfaceSpecV1.model_validate(raw)


# --------------------------------------------------------------------------- #
# 6. JSON Schema export smoke check                                           #
# --------------------------------------------------------------------------- #


def test_json_schema_has_expected_top_level_fields() -> None:
    schema = SurfaceSpecV1.model_json_schema(mode="serialization")
    props = schema.get("properties", {})
    for required in (
        "schema_version",
        "surface_id",
        "turn_id",
        "run_id",
        "intent",
        "budget_hint",
        "block_compat",
        "blocks",
        "fallback_text",
    ):
        assert required in props, f"missing top-level field {required!r} in JSON Schema"


def test_exported_schema_file_in_sync_if_present() -> None:
    """When the on-disk schema exists, it must match the generated one.

    We don't fail if it's missing — the export script generates it. But if it's
    there (CI common case), it must match exactly.
    """
    repo_root = Path(__file__).resolve().parent.parent.parent
    output = repo_root / "frontend" / "lib" / "surface.schema.json"
    if not output.exists():
        pytest.skip(f"{output} not generated yet")

    # Reuse the exporter's serialization to avoid drift.
    import importlib.util
    spec_path = repo_root / "scripts" / "export_surface_schema.py"
    module_spec = importlib.util.spec_from_file_location("export_surface_schema", spec_path)
    assert module_spec and module_spec.loader
    mod = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(mod)

    expected = mod.serialize(mod.build_schema())
    actual = output.read_text(encoding="utf-8")
    assert actual == expected, (
        "frontend/lib/surface.schema.json is stale; "
        "run `python scripts/export_surface_schema.py`"
    )


# --------------------------------------------------------------------------- #
# 7. Defensive: SurfaceBlock alone validates data shape (used by composers)   #
# --------------------------------------------------------------------------- #


def test_surface_block_validates_shape_standalone() -> None:
    block = SurfaceBlock.model_validate(
        {
            "id": "h",
            "type": "heading",
            "data": {"text": "Hello", "severity": "info"},
            "fallback_text": "Hello.",
        }
    )
    assert block.type == SurfaceBlockType.heading
    parsed = block.parsed_data()
    assert parsed.model_dump()["text"] == "Hello"
