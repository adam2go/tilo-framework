from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


CORE_BLOCK_TYPES = {
    "markdown",
    "table",
    "form",
    "approval_card",
    "risk_panel",
    "metric",
    "list",
}

KNOWN_EXTENSION_BLOCK_TYPES = {
    "rich_text",
    "card",
    "risk_summary",
    "risk_review_panel",
    "metric_dashboard",
    "memory_candidate_card",
    "tool_call_preview",
    "action_queue",
    "editable_document_preview",
    "editable_document_placeholder",
    "timeline",
    "kanban",
    "risk_item",
    "citation",
    "comparison_matrix",
    "confirmation_action",
    # Domain-specialised blocks. They are still pure presentation — the
    # Canvas picks an appropriate renderer based on type. Agents / demos
    # opt into these by emitting them from an ArtifactSpecBuilder; the
    # generic Canvas still works without any of them.
    "clause_reader",
    "risk_radar",
    "revision_diff",
}

SUPPORTED_BLOCK_TYPES = CORE_BLOCK_TYPES | KNOWN_EXTENSION_BLOCK_TYPES

SUPPORTED_ACTION_TYPES = {
    "approve",
    "reject",
    "edit",
    "select",
    "continue_task",
    "regenerate",
    "invoke_tool",
    "create_memory",
    "promote_skill",
    "export",
    "confirm",
}

SUPPORTED_STATE_ENTITIES = {
    "artifact",
    "confirmation",
    "memory",
    "skill_candidate",
    "tool_invocation",
    "task",
    "run",
}


class StateBinding(BaseModel):
    entity_type: str
    entity_id: str
    field: str | None = None

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, value: str) -> str:
        if value not in SUPPORTED_STATE_ENTITIES:
            raise ValueError(f"Unsupported state binding entity type: {value}")
        return value


class ArtifactAction(BaseModel):
    id: str
    label: str
    action_type: str
    confirmation_required: bool = False
    confirmation_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    state_binding: StateBinding | None = None

    @field_validator("action_type")
    @classmethod
    def validate_action_type(cls, value: str) -> str:
        if value not in SUPPORTED_ACTION_TYPES:
            raise ValueError(f"Unsupported artifact action type: {value}")
        return value


class ArtifactBlock(BaseModel):
    id: str
    type: str
    title: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    actions: list[ArtifactAction] = Field(default_factory=list)
    state_binding: StateBinding | None = None

    @field_validator("type")
    @classmethod
    def validate_block_type(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Artifact block type is required")
        return value


class ProvenanceRef(BaseModel):
    type: str
    id: str
    label: str | None = None


class ArtifactView(BaseModel):
    """One Canvas tab declared by the artifact author.

    A view groups a subset of the artifact's blocks under a label / icon and
    optionally hands rendering off to a domain-specialised renderer.

    Why this lives on ArtifactSpec rather than on Canvas:
      - The artifact author (an ArtifactSpecBuilder for a specific agent
        type) knows which blocks belong together. The Canvas should not
        guess.
      - Agents we haven't built yet can declare their own views without
        any frontend change. The renderer falls back to "stack the blocks
        listed by `block_ids`" when no renderer hint is provided.

    Optional fields:
      - `block_ids`: which blocks from `ArtifactSpec.blocks` show in this
        view. Empty/omitted → all blocks are eligible.
      - `renderer`: hint for a specialised view renderer
        (e.g. "clause_reader" pulls a single clause_reader block to fill
        the whole tab). If omitted, a default block-list renderer is used.
      - `icon`: lucide-style icon name. Frontend maps unknown icons to a
        default.
      - `description`: optional one-liner shown in the tab header.
    """

    id: str
    label: str
    icon: str | None = None
    description: str | None = None
    block_ids: list[str] = Field(default_factory=list)
    renderer: str | None = None

    @field_validator("id", "label")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Artifact view id and label are required")
        return value


class ArtifactSpecV1(BaseModel):
    version: Literal["artifact_spec.v1"] = "artifact_spec.v1"
    artifact_type: str
    title: str
    status: Literal["draft", "streaming", "ready", "failed"] = "ready"
    blocks: list[ArtifactBlock]
    actions: list[ArtifactAction] = Field(default_factory=list)
    provenance: list[ProvenanceRef] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    run_id: str | None = None
    # Optional Canvas tab declarations. When omitted, the Canvas renders
    # all blocks under a single "Result" tab. Validation is intentionally
    # lenient — the agent may reference block ids that don't exist yet
    # (e.g. for streaming artifacts) and the frontend skips them
    # gracefully. This keeps backwards compatibility: every existing
    # artifact in the database remains valid.
    views: list[ArtifactView] = Field(default_factory=list)
    # AI-generated follow-up suggestions based on the artifact content.
    # The frontend displays these as "猜你想问" chips after a run completes.
    follow_ups: list[str] = Field(default_factory=list)

    @field_validator("artifact_type")
    @classmethod
    def validate_artifact_type(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("artifact_type is required")
        return value

    @field_validator("blocks")
    @classmethod
    def validate_blocks(cls, value: list[ArtifactBlock]) -> list[ArtifactBlock]:
        if not value:
            raise ValueError("Artifact must include at least one block")
        return value
