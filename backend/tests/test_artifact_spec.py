from helpers import *  # noqa: F401,F403


def test_artifact_schema_accepts_roam_actions_and_state_binding() -> None:
    spec = ArtifactSpecV1.model_validate(
        {
            "artifact_type": "demo",
            "title": "ROAM Demo",
            "blocks": [
                {
                    "id": "approval",
                    "type": "approval_card",
                    "data": {"title": "Approve"},
                    "state_binding": {"entity_type": "run", "entity_id": "run-1"},
                    "actions": [
                        {
                            "id": "approve",
                            "label": "Approve",
                            "action_type": "approve",
                            "confirmation_required": True,
                            "state_binding": {"entity_type": "confirmation", "entity_id": "confirmation-1"},
                        }
                    ],
                }
            ],
        }
    )

    assert spec.blocks[0].type == "approval_card"
    assert spec.blocks[0].actions[0].action_type == "approve"
    assert spec.blocks[0].state_binding.entity_type == "run"


def test_artifact_schema_core_blocks_and_extension_blocks_are_stable() -> None:
    assert {"markdown", "table", "form", "approval_card", "risk_panel", "metric", "list"}.issubset(CORE_BLOCK_TYPES)

    spec = ArtifactSpecV1.model_validate(
        {
            "artifact_type": "demo",
            "title": "Extension Demo",
            "blocks": [
                {"id": "core", "type": "risk_panel", "data": {"summary": "Core risk panel"}},
                {"id": "extension", "type": "sales_followup_sequence", "data": {"summary": "Extension block"}},
            ],
        }
    )

    assert spec.blocks[0].type == "risk_panel"
    assert spec.blocks[1].type == "sales_followup_sequence"
