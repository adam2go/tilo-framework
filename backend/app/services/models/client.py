import asyncio
import json
from typing import Any

import httpx

from app.core.config import Settings
from app.services.models.errors import ModelDisabledError, ModelInvalidJSONError, ModelProviderError, ModelTimeoutError


OPENAI_COMPATIBLE_DEFAULTS = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com",
    "google": "https://generativelanguage.googleapis.com/v1beta/openai",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "xai": "https://api.x.ai/v1",
    "mistral": "https://api.mistral.ai/v1",
    "groq": "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "together": "https://api.together.xyz/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "tencent": "https://tokenhub.tencentmaas.com/v1",
    "tencent_deepseek": "https://tokenhub.tencentmaas.com/v1",
    "moonshot": "https://api.moonshot.ai/v1",
    "kimi": "https://api.moonshot.ai/v1",
    "zhipu": "https://open.bigmodel.cn/api/paas/v4",
    "glm": "https://open.bigmodel.cn/api/paas/v4",
    "azure_openai": "",
    "custom": "",
    "openai_compatible": "",
}

PROVIDER_API_KEY_FIELDS = {
    "openai": "openai_api_key",
    "anthropic": "anthropic_api_key",
    "claude": "anthropic_api_key",
    "deepseek": "deepseek_api_key",
    "google": "google_api_key",
    "gemini": "google_api_key",
    "xai": "xai_api_key",
    "mistral": "mistral_api_key",
    "groq": "groq_api_key",
    "openrouter": "openrouter_api_key",
    "together": "together_api_key",
    "qwen": "qwen_api_key",
    "dashscope": "qwen_api_key",
    "tencent": "tencent_api_key",
    "tencent_deepseek": "tencent_api_key",
    "moonshot": "moonshot_api_key",
    "kimi": "moonshot_api_key",
    "zhipu": "zhipu_api_key",
    "glm": "zhipu_api_key",
}


class ModelClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def enabled(self) -> bool:
        return bool(self.settings.llm_enabled and self.api_key)

    @property
    def provider(self) -> str:
        return (self.settings.llm_provider or "openai").strip().lower()

    @property
    def provider_family(self) -> str:
        return "anthropic" if self.provider in {"anthropic", "claude"} else "openai_compatible"

    @property
    def api_key(self) -> str:
        if self.settings.llm_api_key:
            return self.settings.llm_api_key
        provider_key_field = PROVIDER_API_KEY_FIELDS.get(self.provider)
        if provider_key_field:
            value = getattr(self.settings, provider_key_field, "")
            if value:
                return value
        if self.provider == "openai" and self.settings.openai_api_key:
            return self.settings.openai_api_key
        return self.settings.openai_api_key

    @property
    def base_url(self) -> str:
        if self.settings.llm_base_url:
            return self.settings.llm_base_url.rstrip("/")
        if self.provider == "openai" and self.settings.openai_base_url:
            return self.settings.openai_base_url.rstrip("/")
        if self.provider in {"anthropic", "claude"}:
            return "https://api.anthropic.com/v1"
        return (OPENAI_COMPATIBLE_DEFAULTS.get(self.provider) or self.settings.openai_base_url).rstrip("/")

    @property
    def provider_slug(self) -> str:
        return "anthropic" if self.provider in {"anthropic", "claude"} else self.provider

    def assert_enabled(self) -> None:
        if not self.settings.llm_enabled:
            raise ModelDisabledError("LLM mode is disabled")
        if not self.api_key:
            raise ModelDisabledError("LLM mode requires LLM_API_KEY or a provider-specific API key")
        if not self.base_url:
            raise ModelDisabledError("LLM mode requires LLM_BASE_URL for this provider")

    async def chat_json(
        self,
        *,
        system: str,
        user: str,
        schema_name: str,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        json_user = f"{user}\n\nReturn valid JSON only. Do not include markdown fences or commentary."
        if self.provider_family == "anthropic":
            text = await self.chat_text(system=system, user=json_user, temperature=temperature)
        else:
            try:
                text = await self.chat_text(system=system, user=json_user, temperature=temperature, response_format={"type": "json_object"})
            except ModelProviderError:
                text = await self.chat_text(system=system, user=json_user, temperature=temperature)
        try:
            parsed = json.loads(_strip_json_fence(text))
        except json.JSONDecodeError as exc:
            raise ModelInvalidJSONError(f"Model returned invalid JSON for {schema_name}") from exc
        if not isinstance(parsed, dict):
            raise ModelInvalidJSONError(f"Model returned non-object JSON for {schema_name}")
        return parsed

    async def chat_text(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.2,
        response_format: dict[str, str] | None = None,
    ) -> str:
        self.assert_enabled()
        if self.provider_family == "anthropic":
            return await self._chat_text_anthropic(system=system, user=user, temperature=temperature)
        return await self._chat_text_openai_compatible(system=system, user=user, temperature=temperature, response_format=response_format)

    async def _chat_text_openai_compatible(
        self,
        *,
        system: str,
        user: str,
        temperature: float,
        response_format: dict[str, str] | None = None,
    ) -> str:
        url = f"{self.base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": self.settings.default_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
        }
        if response_format:
            payload["response_format"] = response_format

        data = await self._post_json(url, payload, headers={"Authorization": f"Bearer {self.api_key}"})
        content = data["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise ModelProviderError("Model provider returned empty content")
        return content

    async def _chat_text_anthropic(self, *, system: str, user: str, temperature: float) -> str:
        url = f"{self.base_url}/messages"
        payload: dict[str, Any] = {
            "model": self.settings.default_model,
            "max_tokens": 1800,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "temperature": temperature,
        }
        data = await self._post_json(
            url,
            payload,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        content = data.get("content") or []
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                parts.append(item["text"])
        text = "\n".join(parts).strip()
        if not text:
            raise ModelProviderError("Anthropic provider returned empty content")
        return text

    async def _post_json(self, url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(max(1, self.settings.llm_max_retries + 1)):
            try:
                async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds) as client:
                    response = await client.post(url, headers=headers, json=payload)
                if response.status_code >= 400:
                    raise ModelProviderError(f"Model provider error: HTTP {response.status_code}")
                return response.json()
            except httpx.TimeoutException as exc:
                last_error = ModelTimeoutError("Model request timed out")
            except ModelProviderError as exc:
                last_error = exc
            except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
                last_error = ModelProviderError(exc.__class__.__name__)
            if attempt < self.settings.llm_max_retries:
                await asyncio.sleep(0.2 * (attempt + 1))
        if last_error:
            raise last_error
        raise ModelProviderError("Model request failed")

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider": self.provider_slug,
            "provider_family": self.provider_family,
            "base_url": self.base_url,
            "enabled": self.enabled,
            "configured": bool(self.api_key),
            "supported_providers": sorted({"anthropic", *OPENAI_COMPATIBLE_DEFAULTS.keys()}),
        }

    def chat_json_sync(self, **kwargs: Any) -> dict[str, Any]:
        return asyncio.run(self.chat_json(**kwargs))

    def chat_text_sync(self, **kwargs: Any) -> str:
        return asyncio.run(self.chat_text(**kwargs))


def _strip_json_fence(value: str) -> str:
    text = value.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text
