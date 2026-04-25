from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


SUPPORTED_BLOCK_TYPES = {
    "markdown",
    "rich_text",
    "table",
    "metric",
    "card",
    "list",
    "timeline",
    "kanban",
    "risk_item",
    "citation",
    "form",
    "comparison_matrix",
    "confirmation_action",
}

SUPPORTED_ACTION_TYPES = {"confirm", "edit", "regenerate", "export", "continue_task"}


class ArtifactBlock(BaseModel):
    id: str
    type: str
    title: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)

    @field_validator("type")
    @classmethod
    def validate_block_type(cls, value: str) -> str:
        if value not in SUPPORTED_BLOCK_TYPES:
            raise ValueError(f"Unsupported artifact block type: {value}")
        return value


class ArtifactAction(BaseModel):
    id: str
    label: str
    action_type: Literal["confirm", "edit", "regenerate", "export", "continue_task"]
    confirmation_required: bool = False
    confirmation_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


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
