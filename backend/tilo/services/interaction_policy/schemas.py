"""Interaction policy schemas.

Phase 1 evolution: rules MAY emit a renderer-agnostic `intent` (preferred)
or a legacy `surface` (renderer component name; deprecated). At least one
of the two MUST be present when the decision is `mini_surface` or
`rich_surface`.

The legacy `surface` form is auto-mapped to an `intent` via
`LEGACY_SURFACE_TO_INTENT` so callers always receive both fields.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from tilo.schemas.surface import SurfaceIntent


class InteractionDecisionType(StrEnum):
    no_ui = "no_ui"
    mini_surface = "mini_surface"
    rich_surface = "rich_surface"
    ask_text = "ask_text"


# Mapping from legacy renderer-component names to Surface Protocol intents.
# Used to translate older policy YAML written before Phase 1 of the refactor.
# See docs/SURFACE_PROTOCOL.md §9 (artifact_spec.v1 mapping) for context.
LEGACY_SURFACE_TO_INTENT: dict[str, SurfaceIntent] = {
    # Mini surfaces
    "MiniIssueCard": SurfaceIntent.request_approval,
    "MiniApprovalCard": SurfaceIntent.request_approval,
    "MiniRevisionPreview": SurfaceIntent.present_result,
    "MiniMemoryCard": SurfaceIntent.confirm_memory,
    "MiniToolPreview": SurfaceIntent.request_approval,
    "MiniChoiceCard": SurfaceIntent.offer_choices,
    # Rich surfaces (any rich surface escalates to a full artifact view)
    "ContractReviewArtifact": SurfaceIntent.escalate_to_rich,
    "FollowupDraftArtifact": SurfaceIntent.escalate_to_rich,
}


class InteractionPolicyBudget(BaseModel):
    max_mini_surfaces_per_run: int = 3
    max_confirmations_per_run: int = 2
    max_memory_cards_per_run: int = 1


class InteractionRule(BaseModel):
    id: str
    when: dict[str, Any] = Field(default_factory=dict)
    decision: InteractionDecisionType
    intent: SurfaceIntent | None = None
    surface: str | None = None  # legacy alias; deprecated
    reason: str

    @model_validator(mode="after")
    def _normalise_intent_or_surface(self) -> "InteractionRule":
        # 1. Both decisions that produce a UI must declare *some* target.
        ui_decisions = {InteractionDecisionType.mini_surface, InteractionDecisionType.rich_surface}
        if self.decision in ui_decisions and self.intent is None and self.surface is None:
            raise ValueError(
                f"Rule {self.id!r}: decision={self.decision.value} requires either 'intent' "
                f"or legacy 'surface'."
            )

        # 2. If a legacy `surface` is given without `intent`, derive intent
        #    from the well-known mapping when possible. Unknown surface names
        #    are tolerated at schema load time — `validate_for_app` is the
        #    proper place to reject them, so app-level surface validation
        #    can produce a clearer error message. We fall back to a generic
        #    intent (`escalate_to_rich` for rich, `present_result` for mini)
        #    so the rule remains evaluable.
        if self.intent is None and self.surface is not None:
            mapped = LEGACY_SURFACE_TO_INTENT.get(self.surface)
            if mapped is None:
                if self.decision == InteractionDecisionType.rich_surface:
                    mapped = SurfaceIntent.escalate_to_rich
                else:
                    mapped = SurfaceIntent.present_result
            self.intent = mapped

        # 3. `no_ui` and `ask_text` rules MUST NOT have intent or surface set.
        if self.decision in {InteractionDecisionType.no_ui, InteractionDecisionType.ask_text}:
            if self.surface is not None:
                raise ValueError(
                    f"Rule {self.id!r}: decision={self.decision.value} must not declare a surface."
                )
            if self.intent is not None:
                raise ValueError(
                    f"Rule {self.id!r}: decision={self.decision.value} must not declare an intent."
                )

        return self


class InteractionPolicy(BaseModel):
    id: str
    version: str
    budget: InteractionPolicyBudget = Field(default_factory=InteractionPolicyBudget)
    rules: list[InteractionRule] = Field(default_factory=list)


class InteractionContext(BaseModel):
    artifact_type: str | None = None
    risk_level: str | None = None
    requires_user_decision: bool | None = None
    category: str | None = None
    user_action: str | None = None
    signal: str | None = None
    mini_surfaces_used: int = Field(default=0, description="Caller-supplied Round 1.5 counter; not yet backend-persisted.")
    confirmations_used: int = Field(default=0, description="Caller-supplied Round 1.5 counter; not yet backend-persisted.")
    memory_cards_used: int = Field(default=0, description="Caller-supplied Round 1.5 counter; not yet backend-persisted.")
    extra: dict[str, Any] = Field(default_factory=dict)


class InteractionDecision(BaseModel):
    decision: InteractionDecisionType
    intent: SurfaceIntent | None = None
    surface: str | None = None  # legacy passthrough; populated when source rule used `surface:`
    reason: str
    rule_id: str | None = None
