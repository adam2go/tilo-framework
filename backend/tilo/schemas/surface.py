"""Tilo Surface Protocol v1 — Pydantic models.

This module is the single source of truth for the Surface Protocol.
The companion JSON Schema (frontend/lib/surface.schema.json) is generated
from these models via tools/export_surface_schema.py.

See docs/SURFACE_PROTOCOL.md for the normative human-readable spec.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from tilo.schemas.artifact import (
    ArtifactAction,
    ProvenanceRef,
    StateBinding,
    SUPPORTED_ACTION_TYPES,  # re-exported for downstream code
)

SURFACE_SCHEMA_VERSION: Literal["tilo.surface.v1"] = "tilo.surface.v1"


# --------------------------------------------------------------------------- #
# Intent vocabulary (closed)                                                  #
# --------------------------------------------------------------------------- #


class SurfaceIntent(StrEnum):
    request_approval = "request_approval"
    collect_input = "collect_input"
    present_result = "present_result"
    offer_choices = "offer_choices"
    confirm_memory = "confirm_memory"
    show_progress = "show_progress"
    escalate_to_rich = "escalate_to_rich"
    ask_clarification = "ask_clarification"


class BudgetHint(StrEnum):
    mini = "mini"
    rich = "rich"


class BlockCompat(StrEnum):
    graceful = "graceful"
    strict = "strict"


# Reserved option action_id meaning "no backend action; client-side only".
NOOP_ACTION_ID = "__noop__"


# --------------------------------------------------------------------------- #
# Block-type vocabulary (closed)                                              #
# --------------------------------------------------------------------------- #


class SurfaceBlockType(StrEnum):
    heading = "heading"
    text = "text"
    evidence = "evidence"
    comparison = "comparison"
    decision = "decision"
    form = "form"
    progress = "progress"
    list = "list"  # noqa: A003 — closed enum value, intentional
    link = "link"
    editable = "editable"
    artifact_link = "artifact_link"
    fallback = "fallback"


class Severity(StrEnum):
    info = "info"
    low = "low"
    medium = "medium"
    high = "high"


class ProgressState(StrEnum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"
    skipped = "skipped"


class FormFieldKind(StrEnum):
    text = "text"
    number = "number"
    textarea = "textarea"
    select = "select"
    toggle = "toggle"
    date = "date"


class LinkTarget(StrEnum):
    drawer = "drawer"
    page = "page"
    webview = "webview"
    external = "external"


class EditableKind(StrEnum):
    rich_text = "rich_text"
    structured = "structured"


# --------------------------------------------------------------------------- #
# Per-block data shapes                                                       #
# --------------------------------------------------------------------------- #


class _StrictModel(BaseModel):
    """Disallow unknown fields inside block.data shapes — closes the schema."""

    model_config = ConfigDict(extra="forbid")


class HeadingData(_StrictModel):
    text: str = Field(min_length=1)
    severity: Severity | None = None


class TextData(_StrictModel):
    content: str = Field(min_length=1)


class EvidenceData(_StrictModel):
    excerpt: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)
    source_label: str | None = None


class ComparisonSide(_StrictModel):
    label: str = Field(min_length=1)
    value: str = Field(min_length=1)
    severity: Severity | None = None


class ComparisonRow(_StrictModel):
    label: str = Field(min_length=1)
    left: str
    right: str
    severity: Severity | None = None


class ComparisonData(_StrictModel):
    shape: Literal["side_by_side", "table"]
    left: ComparisonSide | None = None
    right: ComparisonSide | None = None
    rows: list[ComparisonRow] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_shape(self) -> "ComparisonData":
        if self.shape == "side_by_side":
            if self.left is None or self.right is None:
                raise ValueError("comparison.side_by_side requires both 'left' and 'right'")
            if self.rows:
                raise ValueError("comparison.side_by_side must not include 'rows'")
        else:  # table
            if self.left is not None or self.right is not None:
                raise ValueError("comparison.table must omit 'left'/'right'")
            if not self.rows:
                raise ValueError("comparison.table requires non-empty 'rows'")
        return self


class DecisionMode(StrEnum):
    single = "single"
    multi = "multi"


class DecisionOption(_StrictModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    value: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    severity: Severity | None = None


class DecisionData(_StrictModel):
    prompt: str | None = None
    mode: DecisionMode = DecisionMode.single
    options: list[DecisionOption] = Field(min_length=1)


class FormFieldOption(_StrictModel):
    label: str = Field(min_length=1)
    value: str = Field(min_length=1)


class FormField(_StrictModel):
    name: str = Field(min_length=1)
    label: str = Field(min_length=1)
    kind: FormFieldKind
    required: bool = False
    placeholder: str | None = None
    min: float | None = None
    max: float | None = None
    step: float | None = None
    options: list[FormFieldOption] = Field(default_factory=list)
    default: Any | None = None

    @model_validator(mode="after")
    def _validate_kind(self) -> "FormField":
        if self.kind == FormFieldKind.select and not self.options:
            raise ValueError("form.select fields require non-empty 'options'")
        if self.kind != FormFieldKind.number and (self.min is not None or self.max is not None or self.step is not None):
            raise ValueError("min/max/step are only valid on form.number fields")
        return self


class FormData(_StrictModel):
    fields: list[FormField] = Field(min_length=1)
    submit_action_id: str = Field(min_length=1)


class ProgressShape(StrEnum):
    steps = "steps"
    percent = "percent"
    status = "status"


class ProgressStep(_StrictModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    state: ProgressState


class ProgressData(_StrictModel):
    shape: ProgressShape
    percent: int | None = Field(default=None, ge=0, le=100)
    status: str | None = None
    steps: list[ProgressStep] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_shape(self) -> "ProgressData":
        if self.shape == ProgressShape.steps and not self.steps:
            raise ValueError("progress.steps requires non-empty 'steps'")
        if self.shape == ProgressShape.percent and self.percent is None:
            raise ValueError("progress.percent requires 'percent'")
        if self.shape == ProgressShape.status and not self.status:
            raise ValueError("progress.status requires 'status'")
        return self


class ListItem(_StrictModel):
    text: str = Field(min_length=1)
    severity: Severity | None = None


class ListData(_StrictModel):
    ordered: bool = False
    items: list[ListItem] = Field(min_length=1)


class LinkData(_StrictModel):
    label: str = Field(min_length=1)
    url: str = Field(min_length=1)
    target: LinkTarget = LinkTarget.external


class EditableData(_StrictModel):
    kind: EditableKind
    value: str
    schema_: dict[str, Any] | None = Field(default=None, alias="schema")
    submit_action_id: str = Field(min_length=1)
    highlights: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @model_validator(mode="after")
    def _validate_kind(self) -> "EditableData":
        if self.kind == EditableKind.structured and self.schema_ is None:
            raise ValueError("editable.structured requires 'schema'")
        return self


class ArtifactLinkData(_StrictModel):
    artifact_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str | None = None
    open_action_id: str = Field(min_length=1)


class FallbackData(_StrictModel):
    content: str = Field(min_length=1)


# --------------------------------------------------------------------------- #
# Block envelope                                                              #
# --------------------------------------------------------------------------- #


_BLOCK_TYPE_TO_DATA: dict[SurfaceBlockType, type[_StrictModel]] = {
    SurfaceBlockType.heading: HeadingData,
    SurfaceBlockType.text: TextData,
    SurfaceBlockType.evidence: EvidenceData,
    SurfaceBlockType.comparison: ComparisonData,
    SurfaceBlockType.decision: DecisionData,
    SurfaceBlockType.form: FormData,
    SurfaceBlockType.progress: ProgressData,
    SurfaceBlockType.list: ListData,
    SurfaceBlockType.link: LinkData,
    SurfaceBlockType.editable: EditableData,
    SurfaceBlockType.artifact_link: ArtifactLinkData,
    SurfaceBlockType.fallback: FallbackData,
}


class SurfaceBlock(BaseModel):
    """One block in a SurfaceSpec.

    `data` is validated against the type-specific shape in `_BLOCK_TYPE_TO_DATA`.
    On validation, `data` is normalized to the *parsed* model dump so downstream
    code can rely on shape stability.
    """

    id: str = Field(min_length=1)
    type: SurfaceBlockType
    data: dict[str, Any] = Field(default_factory=dict)
    fallback_text: str = Field(min_length=1)
    actions: list[ArtifactAction] = Field(default_factory=list)
    state_binding: StateBinding | None = None

    model_config = ConfigDict(use_enum_values=False)

    @model_validator(mode="after")
    def _validate_data_shape(self) -> "SurfaceBlock":
        shape_cls = _BLOCK_TYPE_TO_DATA[self.type]
        parsed = shape_cls.model_validate(self.data)
        self.data = parsed.model_dump(by_alias=True, exclude_none=False)
        return self

    # Convenient parsed-data accessor
    def parsed_data(self) -> _StrictModel:
        return _BLOCK_TYPE_TO_DATA[self.type].model_validate(self.data)


# --------------------------------------------------------------------------- #
# Channel-fallback hints                                                      #
# --------------------------------------------------------------------------- #


class TelegramFallback(BaseModel):
    inline_keyboard: list[list[dict[str, Any]]] = Field(default_factory=list)


class SlackFallback(BaseModel):
    blocks: list[dict[str, Any]] = Field(default_factory=list)


class EmailFallback(BaseModel):
    html: str = Field(min_length=1)


class SurfaceFallbacks(BaseModel):
    telegram: TelegramFallback | None = None
    slack: SlackFallback | None = None
    email: EmailFallback | None = None

    model_config = ConfigDict(extra="allow")  # forward-compatible for new channels


# --------------------------------------------------------------------------- #
# Top-level SurfaceSpec                                                       #
# --------------------------------------------------------------------------- #


class SurfaceSpecV1(BaseModel):
    schema_version: Literal["tilo.surface.v1"] = SURFACE_SCHEMA_VERSION
    surface_id: str = Field(min_length=1)
    turn_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)

    intent: SurfaceIntent
    budget_hint: BudgetHint
    block_compat: BlockCompat = BlockCompat.graceful

    blocks: Annotated[list[SurfaceBlock], Field(min_length=1)]
    fallback_text: str = Field(min_length=1)
    fallbacks: SurfaceFallbacks | None = None

    provenance: list[ProvenanceRef] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=False)

    # ---- Cross-block validation (rules 7-8 of §7) ------------------------- #

    @model_validator(mode="after")
    def _validate_action_refs(self) -> "SurfaceSpecV1":
        seen_block_ids: set[str] = set()
        for block in self.blocks:
            if block.id in seen_block_ids:
                raise ValueError(f"Duplicate block id: {block.id!r}")
            seen_block_ids.add(block.id)

            available_action_ids = {a.id for a in block.actions}

            if block.type == SurfaceBlockType.decision:
                data = DecisionData.model_validate(block.data)
                self._check_action_refs(
                    block_id=block.id,
                    refs={opt.action_id for opt in data.options},
                    available=available_action_ids,
                    field="decision.option.action_id",
                )

            elif block.type == SurfaceBlockType.form:
                data = FormData.model_validate(block.data)
                self._check_action_refs(
                    block_id=block.id,
                    refs={data.submit_action_id},
                    available=available_action_ids,
                    field="form.submit_action_id",
                )

            elif block.type == SurfaceBlockType.editable:
                data = EditableData.model_validate(block.data)
                self._check_action_refs(
                    block_id=block.id,
                    refs={data.submit_action_id},
                    available=available_action_ids,
                    field="editable.submit_action_id",
                )

            elif block.type == SurfaceBlockType.artifact_link:
                data = ArtifactLinkData.model_validate(block.data)
                self._check_action_refs(
                    block_id=block.id,
                    refs={data.open_action_id},
                    available=available_action_ids,
                    field="artifact_link.open_action_id",
                )
        return self

    @staticmethod
    def _check_action_refs(
        *, block_id: str, refs: set[str], available: set[str], field: str
    ) -> None:
        for ref in refs:
            if ref == NOOP_ACTION_ID:
                continue
            if ref not in available:
                raise ValueError(
                    f"Block {block_id!r} {field} references missing action_id {ref!r}; "
                    f"available actions: {sorted(available) or '[]'}"
                )

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str) -> str:
        if value != SURFACE_SCHEMA_VERSION:
            raise ValueError(f"Unsupported schema_version: {value!r}; expected {SURFACE_SCHEMA_VERSION!r}")
        return value


__all__ = [
    "SURFACE_SCHEMA_VERSION",
    "NOOP_ACTION_ID",
    "SurfaceIntent",
    "BudgetHint",
    "BlockCompat",
    "SurfaceBlockType",
    "Severity",
    "ProgressState",
    "FormFieldKind",
    "LinkTarget",
    "EditableKind",
    "DecisionMode",
    "ProgressShape",
    "HeadingData",
    "TextData",
    "EvidenceData",
    "ComparisonData",
    "ComparisonSide",
    "ComparisonRow",
    "DecisionData",
    "DecisionOption",
    "FormData",
    "FormField",
    "FormFieldOption",
    "ProgressData",
    "ProgressStep",
    "ListData",
    "ListItem",
    "LinkData",
    "EditableData",
    "ArtifactLinkData",
    "FallbackData",
    "SurfaceBlock",
    "SurfaceFallbacks",
    "TelegramFallback",
    "SlackFallback",
    "EmailFallback",
    "SurfaceSpecV1",
]
