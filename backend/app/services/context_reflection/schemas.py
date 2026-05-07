from typing import Any, Literal

from pydantic import BaseModel, Field


class ORIDObjective(BaseModel):
    facts: list[str] = Field(default_factory=list)


class ORIDReflective(BaseModel):
    signals: list[str] = Field(default_factory=list)


class ORIDInterpretive(BaseModel):
    insights: list[str] = Field(default_factory=list)


class ORIDDecisionalAction(BaseModel):
    action: Literal["propose_memory", "none"] = "none"
    content: str | None = None
    memory_type: str | None = None
    why: str = ""
    evidence: list[str] = Field(default_factory=list)


class ContextReflectionResult(BaseModel):
    objective: ORIDObjective = Field(default_factory=ORIDObjective)
    reflective: ORIDReflective = Field(default_factory=ORIDReflective)
    interpretive: ORIDInterpretive = Field(default_factory=ORIDInterpretive)
    decisional: list[ORIDDecisionalAction] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
