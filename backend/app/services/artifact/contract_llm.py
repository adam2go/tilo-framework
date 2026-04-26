from dataclasses import dataclass

from pydantic import ValidationError

from app.core.config import Settings
from app.models import Memory, Task
from app.services.models.client import ModelClient
from app.services.models.errors import ModelClientError
from app.services.models.prompts import CONTRACT_REVIEW_SYSTEM_PROMPT, contract_review_user_prompt
from app.services.models.schemas import ContractReviewLLMData


@dataclass
class ContractReviewLLMResult:
    status: str
    mode: str
    model: str
    data: ContractReviewLLMData | None = None
    fallback_reason: str | None = None


class ContractReviewLLMGenerator:
    def __init__(self, settings: Settings, client: ModelClient | None = None) -> None:
        self.settings = settings
        self.client = client or ModelClient(settings)

    def generate(self, task: Task, memories: list[Memory], tool_outputs: list[dict]) -> ContractReviewLLMResult:
        if not self.client.enabled:
            reason = "disabled" if not self.settings.llm_enabled else "missing_api_key"
            return ContractReviewLLMResult(status="fallback", mode="deterministic", model=self.settings.default_model, fallback_reason=reason)

        memory_snippets = [memory.content for memory in memories[:5]]
        try:
            raw = self.client.chat_json_sync(
                system=CONTRACT_REVIEW_SYSTEM_PROMPT,
                user=contract_review_user_prompt(task.input_message, memory_snippets, tool_outputs),
                schema_name="contract_review_llm_data",
                temperature=0.2,
            )
            data = ContractReviewLLMData.model_validate(raw)
        except (ModelClientError, ValidationError, ValueError) as exc:
            return ContractReviewLLMResult(
                status="fallback",
                mode="deterministic",
                model=self.settings.default_model,
                fallback_reason=exc.__class__.__name__,
            )
        return ContractReviewLLMResult(status="success", mode="llm", model=self.settings.default_model, data=data)
