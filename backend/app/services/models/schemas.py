from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ContractRisk(BaseModel):
    id: str
    clause: str
    risk_level: Literal["high", "medium", "low"]
    issue: str
    suggested_revision: str
    evidence: str = ""


class ContractRiskSummary(BaseModel):
    high_count: int = Field(default=0, ge=0, le=20)
    medium_count: int = Field(default=0, ge=0, le=20)
    low_count: int = Field(default=0, ge=0, le=20)
    summary: str


class ContractRevisionDraft(BaseModel):
    heading: str = "Conservative revision draft"
    content: str
    highlights: list[str] = Field(default_factory=list)


class ContractMemoryCandidate(BaseModel):
    type: str = "preference"
    content: str
    confidence: float = Field(default=0.7, ge=0, le=1)


class ContractReviewLLMData(BaseModel):
    risk_summary: ContractRiskSummary
    risks: list[ContractRisk]
    revision_draft: ContractRevisionDraft
    memory_candidate: ContractMemoryCandidate

    @field_validator("risks")
    @classmethod
    def validate_risks(cls, value: list[ContractRisk]) -> list[ContractRisk]:
        if not value:
            raise ValueError("At least one contract risk is required")
        return value[:5]
