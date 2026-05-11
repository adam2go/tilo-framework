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
