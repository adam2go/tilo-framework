from dataclasses import dataclass
from typing import Callable

from pydantic import ValidationError

from tilo.core.config import Settings
from tilo.models import Memory, Task
from tilo.services.demo import load_problematic_ai_service_agreement
from tilo.services.models.client import ModelClient
from tilo.services.models.errors import ModelClientError
from tilo.services.models.prompts import CONTRACT_REVIEW_SYSTEM_PROMPT, contract_review_user_prompt
from tilo.services.models.schemas import ContractReviewLLMData


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

    def generate(
        self,
        task: Task,
        memories: list[Memory],
        tool_outputs: list[dict],
        on_thinking: Callable[[str], None] | None = None,
        on_content: Callable[[str], None] | None = None,
    ) -> ContractReviewLLMResult:
        if not self.client.enabled:
            reason = "disabled" if not self.settings.llm_enabled else "missing_api_key"
            return ContractReviewLLMResult(status="fallback", mode="deterministic", model=self.settings.default_model, fallback_reason=reason)

        memory_snippets = [memory.content for memory in memories[:5]]

        # Resolve the contract text to inject into the prompt.
        # Priority:
        #   1. If the user's message itself is long (>500 chars) it likely
        #      contains the full contract pasted inline → use as-is.
        #   2. If the message mentions the fixture contract, load it.
        #   3. Otherwise send None — the model will do its best.
        contract_text = self._resolve_contract_text(task.input_message)

        try:
            # Streaming version surfaces reasoning chunks while the model
            # is still working, so the runtime can show "thinking" progress
            # in the trace stream rather than blocking the user on a 60s
            # silent wait. Falls back to the non-streaming method when a
            # client (e.g. test stub) doesn't implement it.
            if hasattr(self.client, "chat_json_streaming_sync"):
                raw = self.client.chat_json_streaming_sync(
                    system=CONTRACT_REVIEW_SYSTEM_PROMPT,
                    user=contract_review_user_prompt(task.input_message, memory_snippets, tool_outputs, contract_text=contract_text),
                    schema_name="contract_review_llm_data",
                    temperature=0.2,
                    on_thinking=on_thinking,
                    on_content=on_content,
                )
            else:
                raw = self.client.chat_json_sync(
                    system=CONTRACT_REVIEW_SYSTEM_PROMPT,
                    user=contract_review_user_prompt(task.input_message, memory_snippets, tool_outputs, contract_text=contract_text),
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

    @staticmethod
    def _resolve_contract_text(message: str) -> str | None:
        """Return the full contract body to inject into the LLM prompt.

        Heuristics:
        1. If the message itself is substantial (>500 chars), the user
           likely pasted the full contract inline → return None so the
           prompt just uses task_message as-is (avoids duplication).
        2. If the message contains keywords that match our fixture
           contract ("AI 客服", "service agreement", "clause 8.1"), load
           the fixture and return its full text.
        3. Otherwise return None — the model gets only the user's short
           instruction. It can still generate a generic review, but
           findings won't reference specific clause numbers.
        """
        if len(message) > 500:
            # User pasted a real contract — it's already in the message.
            return None
        fixture_signals = [
            "AI 客服", "ai service agreement", "service agreement",
            "liability", "indemnity", "8.1", "8.2",
            "合同", "条款", "责任上限", "赔偿",
            "risky clauses", "flag risky",
        ]
        text_lower = message.lower()
        if any(sig.lower() in text_lower for sig in fixture_signals):
            try:
                fixture = load_problematic_ai_service_agreement()
                return fixture.content
            except FileNotFoundError:
                return None
        return None
