from helpers import *  # noqa: F401,F403


def test_artifact_schema_accepts_roam_actions_and_state_binding() -> None:
    spec = ArtifactSpecV1.model_validate(
        {
            "artifact_type": "demo",
            "title": "ROAM Demo",
            "blocks": [
                {
                    "id": "approval",
                    "type": "card",
                    "props": {"title": "Approve"},
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

    assert spec.blocks[0].type == "card"
    assert spec.blocks[0].actions[0].action_type == "approve"
    assert spec.blocks[0].state_binding.entity_type == "run"


def test_artifact_schema_primitive_block_types_are_stable() -> None:
    """Verify the core primitives include expected types."""
    assert {"markdown", "table", "form", "metric", "list", "card", "chart"}.issubset(PRIMITIVE_BLOCK_TYPES)

    spec = ArtifactSpecV1.model_validate(
        {
            "artifact_type": "demo",
            "title": "Extension Demo",
            "blocks": [
                {"id": "core", "type": "card", "props": {"summary": "Core card"}},
                {"id": "extension", "type": "sales_followup_sequence", "props": {"summary": "Extension block"}},
            ],
        }
    )

    assert spec.blocks[0].type == "card"
    assert spec.blocks[1].type == "sales_followup_sequence"


def test_artifact_schema_backward_compat_data_to_props() -> None:
    """Verify that v0.x specs using 'data' are accepted and normalized to 'props'."""
    spec = ArtifactSpecV1.model_validate(
        {
            "version": "artifact_spec.v1",
            "artifact_type": "contract_review",
            "title": "Legacy Test",
            "blocks": [
                {
                    "id": "summary",
                    "type": "approval_card",
                    "data": {"title": "Approve"},
                }
            ],
        }
    )
    # "data" should be normalized to "props"
    assert spec.blocks[0].props == {"title": "Approve"}
    # v0.x version string accepted
    assert spec.version == "artifact_spec.v1"


def test_artifact_schema_aip_v1_version() -> None:
    """Verify the new AIP v1 version string works."""
    spec = ArtifactSpecV1.model_validate(
        {
            "version": "tilo/aip/v1",
            "title": "AIP v1 Test",
            "blocks": [
                {"id": "b1", "type": "markdown", "props": {"content": "Hello"}},
            ],
        }
    )
    assert spec.version == "tilo/aip/v1"
    assert spec.artifact_type == "document"  # default
