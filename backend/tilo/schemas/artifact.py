"""Tilo AIP v1 — Artifact Spec schema.

This is the single source of truth for Tilo's Agent Interaction Protocol
artifact specification. It defines:

  - ~20 primitive block types (inspired by HTML semantic elements)
  - Open extension: any string is a valid block type
  - Views with inline blocks
  - Backward-compat shims for v0.x (data→props alias, artifact_type optional)

See docs/AIP_DESIGN.md for the full design rationale.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

# --------------------------------------------------------------------------- #
# Primitive block types (~20, stable, rarely changed)                          #
# --------------------------------------------------------------------------- #

PRIMITIVE_BLOCK_TYPES = {
    # Content display
    "markdown",      # rich text (like <article>)
    "table",         # columns + rows (like <table>)
    "list",          # ordered / unordered items (like <ul>/<ol>)
    "image",         # image with alt text (like <img>)
    "video",         # embedded video (like <video>)
    "code",          # code block with language hint (like <pre><code>)
    "heading",       # section heading (like <h1>-<h6>)
    # Data visualization
    "metric",        # single KPI value (label + value + trend)
    "chart",         # visualization (props.chart_type: line/bar/pie/radar/...)
    "progress",      # progress bar / step indicator
    # User interaction
    "form",          # input fields + submit
    "button_group",  # action buttons
    # Structured display
    "card",          # generic container with title, content, actions
    "diff",          # before/after comparison
    "timeline",      # chronological sequence
    "kanban",        # column-based board
    "tabs",          # nested tab group (view-in-view)
    # Tilo-native (framework-specific)
    "confirmation",  # action requiring human approval
    "memory_card",   # memory candidate display
    "tool_preview",  # tool call preview with approve/reject
}

# Backward-compat: old type names → new primitive equivalents.
# The validator auto-maps these so existing specs keep working.
_LEGACY_TYPE_MAP: dict[str, str] = {
    "approval_card": "card",
    "risk_panel": "card",
    "rich_text": "markdown",
    "risk_summary": "card",
    "risk_review_panel": "table",
    "metric_dashboard": "metric",
    "memory_candidate_card": "memory_card",
    "tool_call_preview": "tool_preview",
    "action_queue": "list",
    "editable_document_preview": "markdown",
    "editable_document_placeholder": "markdown",
    "risk_item": "card",
    "citation": "markdown",
    "comparison_matrix": "table",
    "confirmation_action": "confirmation",
    # Domain-specific blocks from v0.x demos — kept as-is (open extension)
    # "clause_reader", "risk_radar", "revision_diff" — no mapping needed
}

# Re-export for backward compatibility with code that imports these names
CORE_BLOCK_TYPES = PRIMITIVE_BLOCK_TYPES
KNOWN_EXTENSION_BLOCK_TYPES: set[str] = set()
SUPPORTED_BLOCK_TYPES = PRIMITIVE_BLOCK_TYPES

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
    """One block in an artifact spec.

    The `props` field holds type-specific properties. For backward compat
    with v0.x specs that used `data`, the model accepts either field name
    and normalizes to `props`.
    """

    id: str
    type: str
    title: str | None = None
    props: dict[str, Any] = Field(default_factory=dict)
    # Backward compat: accept "data" as alias for "props"
    data: dict[str, Any] | None = Field(default=None, exclude=True)
    actions: list[ArtifactAction] = Field(default_factory=list)
    state_binding: StateBinding | None = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_data_to_props(cls, values: Any) -> Any:
        """Accept both `data` and `props`; prefer `props` if both present."""
        if isinstance(values, dict):
            if "data" in values and "props" not in values:
                values["props"] = values.pop("data")
            elif "data" in values and "props" in values:
                values.pop("data")  # props wins
        return values

    @field_validator("type")
    @classmethod
    def validate_block_type(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Artifact block type is required")
        # Open extension: any non-empty string is valid.
        # No mapping applied — we keep original type for renderer dispatch.
        return value


class ProvenanceRef(BaseModel):
    type: str
    id: str
    label: str | None = None


class ArtifactView(BaseModel):
    """One Canvas tab declared by the artifact author.

    AIP v1 supports two modes:
      1. Inline blocks: `blocks` contains full ArtifactBlock objects.
         This is the preferred mode for LLM-generated specs.
      2. Block references: `block_ids` lists IDs from the top-level
         blocks array. This is the v0.x mode, kept for backward compat.

    When both are empty, all top-level blocks are shown.
    """

    id: str
    label: str
    icon: str | None = None
    description: str | None = None
    layout: str | None = None  # e.g. "stack", "grid-2col", "grid-3col"
    # v0.x mode: reference block IDs from top-level blocks array
    block_ids: list[str] = Field(default_factory=list)
    # AIP v1 mode: inline block definitions (not yet used, reserved)
    # blocks: list[ArtifactBlock] = Field(default_factory=list)
    renderer: str | None = None

    @field_validator("id", "label")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Artifact view id and label are required")
        return value


class ArtifactSpecV1(BaseModel):
    """Top-level artifact specification.

    Accepts both AIP v1 (`tilo/aip/v1`) and legacy (`artifact_spec.v1`)
    version strings. `artifact_type` is optional in AIP v1 but accepted
    for backward compatibility.
    """

    version: str = "tilo/aip/v1"
    # Optional in AIP v1 — the combination of views/blocks defines shape.
    # Kept for backward compat with v0.x specs.
    artifact_type: str = "document"
    title: str
    status: Literal["draft", "streaming", "ready", "failed"] = "ready"
    blocks: list[ArtifactBlock] = Field(default_factory=list)
    actions: list[ArtifactAction] = Field(default_factory=list)
    provenance: list[ProvenanceRef] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    run_id: str | None = None
    views: list[ArtifactView] = Field(default_factory=list)
    follow_ups: list[str] = Field(default_factory=list)

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        if value not in ("tilo/aip/v1", "artifact_spec.v1"):
            raise ValueError(f"Unsupported spec version: {value!r}")
        return value

    @field_validator("blocks")
    @classmethod
    def validate_blocks(cls, value: list[ArtifactBlock]) -> list[ArtifactBlock]:
        if not value:
            raise ValueError("Artifact must include at least one block")
        return value
