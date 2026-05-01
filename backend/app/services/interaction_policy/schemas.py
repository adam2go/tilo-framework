from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class InteractionDecisionType(StrEnum):
    no_ui = "no_ui"
    mini_surface = "mini_surface"
    rich_surface = "rich_surface"
    ask_text = "ask_text"


class InteractionPolicyBudget(BaseModel):
    max_mini_surfaces_per_run: int = 3
    max_confirmations_per_run: int = 2
    max_memory_cards_per_run: int = 1


class InteractionRule(BaseModel):
    id: str
    when: dict[str, Any] = Field(default_factory=dict)
    decision: InteractionDecisionType
    surface: str | None = None
    reason: str


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
    surface: str | None = None
    reason: str
    rule_id: str | None = None
