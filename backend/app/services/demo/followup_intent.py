from typing import Literal

from pydantic import BaseModel, ValidationError

from app.core.config import Settings
from app.services.models.client import ModelClient
from app.services.models.errors import ModelClientError


FollowUpIntent = Literal[
    "explain_risk",
    "revise_tone",
    "focus_clause",
    "draft_email",
    "remember_preference",
    "general_followup",
]


class FollowUpIntentResult(BaseModel):
    intent: FollowUpIntent
    confidence: float = 0.7
    mode: Literal["llm", "deterministic"] = "deterministic"
    reason: str = ""


class FollowUpIntentClassifier:
    def __init__(self, settings: Settings, client: ModelClient | None = None) -> None:
        self.settings = settings
        self.client = client or ModelClient(settings)

    def classify(self, text: str, locale: str = "en") -> FollowUpIntentResult:
        fallback = classify_followup_deterministic(text, locale)
        if not self.client.enabled:
            return fallback
        try:
            raw = self.client.chat_json_sync(
                system=(
                    "Classify a user's follow-up message in a contract review demo. "
                    "Return JSON only. Do not include secrets, hidden reasoning, markdown, or commentary."
                ),
                user=(
                    f"Locale: {locale}\n"
                    f"Message: {text}\n\n"
                    "Choose exactly one intent from: explain_risk, revise_tone, focus_clause, "
                    "draft_email, remember_preference, general_followup.\n"
                    'Return shape: {"intent": "...", "confidence": 0.8, "reason": "..."}'
                ),
                schema_name="followup_intent",
                temperature=0,
            )
            result = FollowUpIntentResult.model_validate({**raw, "mode": "llm"})
            return result
        except (ModelClientError, ValidationError, ValueError):
            return fallback


def classify_followup_deterministic(text: str, locale: str = "en") -> FollowUpIntentResult:
    normalized = text.strip().lower()
    if not normalized:
        return FollowUpIntentResult(intent="general_followup", confidence=0.5, reason="empty")
    if any(token in normalized for token in ["记住", "记忆", "以后", "remember", "save this", "preference"]):
        return FollowUpIntentResult(intent="remember_preference", confidence=0.82, reason="memory keyword")
    if any(token in normalized for token in ["语气", "强硬", "柔和", "客户", "谈判", "tone", "softer", "friendlier", "friendly", "negotiat"]):
        return FollowUpIntentResult(intent="revise_tone", confidence=0.86, reason="tone keyword")
    if any(token in normalized for token in ["邮件", "email", "mail", "发给", "回复客户"]):
        return FollowUpIntentResult(intent="draft_email", confidence=0.82, reason="email keyword")
    if any(token in normalized for token in ["8.1", "8.2", "条款", "clause", "section"]):
        return FollowUpIntentResult(intent="focus_clause", confidence=0.78, reason="clause keyword")
    if any(token in normalized for token in ["为什么", "解释", "原因", "why", "explain", "meaning", "risk"]):
        return FollowUpIntentResult(intent="explain_risk", confidence=0.74, reason="explanation keyword")
    return FollowUpIntentResult(intent="general_followup", confidence=0.62, reason="fallback")
