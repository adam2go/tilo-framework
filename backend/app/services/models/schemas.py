from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


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
        if len(value) < 3:
            raise ValueError("At least three contract risks are required for the public demo surface")
        priority = {"high": 0, "medium": 1, "low": 2}

        def risk_rank(risk: ContractRisk) -> tuple[int, int]:
            text = f"{risk.id} {risk.clause} {risk.issue}".lower()
            is_liability_conflict = int(not (("8.1" in text and "8.2" in text) or ("liability" in text and "indemn" in text) or ("责任" in text and "赔偿" in text)))
            return (is_liability_conflict, priority[risk.risk_level])

        return sorted(value, key=risk_rank)[:8]

    @model_validator(mode="after")
    def normalize_summary_counts(self) -> "ContractReviewLLMData":
        self.risk_summary.high_count = sum(1 for risk in self.risks if risk.risk_level == "high")
        self.risk_summary.medium_count = sum(1 for risk in self.risks if risk.risk_level == "medium")
        self.risk_summary.low_count = sum(1 for risk in self.risks if risk.risk_level == "low")
        self.revision_draft.highlights = self.revision_draft.highlights[:3]
        return self
