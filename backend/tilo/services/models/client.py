import asyncio
import json
from typing import Any, Callable

import httpx

from tilo.core.config import Settings
from tilo.services.models.errors import ModelDisabledError, ModelInvalidJSONError, ModelProviderError, ModelTimeoutError


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
        # Disable extended thinking on providers/models that default to it
        # (Kimi K2.6, Qwen3-Thinking, etc.). For deterministic structured
        # output we don't need 60-180s of chain-of-thought reasoning.
        if not self.settings.llm_thinking_enabled and self._supports_thinking_toggle():
            payload["thinking"] = {"type": "disabled"}

        try:
            data = await self._post_json(url, payload, headers={"Authorization": f"Bearer {self.api_key}"})
        except ModelProviderError as exc:
            # Some reasoning-only models (e.g. Kimi K2 family on Tencent
            # MaaS) reject any non-default temperature with HTTP 400. Retry
            # once without that field rather than blacklisting models.
            message = str(exc).lower()
            if "temperature" in message or "only 1 is allowed" in message:
                retry_payload = dict(payload)
                retry_payload.pop("temperature", None)
                data = await self._post_json(
                    url, retry_payload, headers={"Authorization": f"Bearer {self.api_key}"}
                )
            elif "thinking" in message:
                # Provider doesn't recognize the thinking field — drop it.
                retry_payload = dict(payload)
                retry_payload.pop("thinking", None)
                data = await self._post_json(
                    url, retry_payload, headers={"Authorization": f"Bearer {self.api_key}"}
                )
            else:
                raise
        content = data["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise ModelProviderError("Model provider returned empty content")
        return content

    def _supports_thinking_toggle(self) -> bool:
        """Whether the active provider/model accepts `thinking.type` field.

        Conservative whitelist — when in doubt we'd rather not send the
        field than risk a 400 from providers that don't know it.
        """
        provider = self.provider
        model = (self.settings.default_model or "").lower()
        if provider in {"moonshot", "kimi"}:
            return True
        if provider in {"tencent", "tencent_deepseek"} and "kimi" in model:
            return True
        if provider in {"qwen", "dashscope"} and ("thinking" in model or "qwq" in model):
            return True
        return False

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
                    snippet = response.text[:240] if response.text else ""
                    raise ModelProviderError(
                        f"Model provider error: HTTP {response.status_code}: {snippet}"
                    )
                return response.json()
            except httpx.TimeoutException:
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

    # ------------------------------------------------------------------ #
    # Streaming                                                           #
    # ------------------------------------------------------------------ #

    async def chat_json_streaming(
        self,
        *,
        system: str,
        user: str,
        schema_name: str,
        temperature: float = 0.2,
        on_thinking: Callable[[str], None] | None = None,
        on_content: Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        """OpenAI-compatible streaming JSON request.

        While the model emits tokens we forward `delta.reasoning_content`
        chunks to `on_thinking` and `delta.content` chunks to `on_content`,
        so the runtime can surface progress to the user *during* the call.
        Once the stream completes we parse the accumulated content as JSON.

        Falls back to the non-streaming path when the provider isn't
        OpenAI-compatible (e.g. Anthropic).
        """
        if self.provider_family == "anthropic":
            # Anthropic's streaming protocol is different and rarely needed
            # for the demos we ship; fall back to non-streaming JSON.
            return await self.chat_json(system=system, user=user, schema_name=schema_name, temperature=temperature)

        self.assert_enabled()
        json_user = f"{user}\n\nReturn valid JSON only. Do not include markdown fences or commentary."
        url = f"{self.base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": self.settings.default_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json_user},
            ],
            "temperature": temperature,
            "stream": True,
            "response_format": {"type": "json_object"},
        }
        if not self.settings.llm_thinking_enabled and self._supports_thinking_toggle():
            payload["thinking"] = {"type": "disabled"}
        try:
            content = await self._stream_openai_compatible(url, payload, on_thinking, on_content)
        except ModelProviderError as exc:
            message = str(exc).lower()
            if "temperature" in message or "only 1 is allowed" in message:
                payload.pop("temperature", None)
                content = await self._stream_openai_compatible(url, payload, on_thinking, on_content)
            elif "response_format" in message or "json_object" in message:
                payload.pop("response_format", None)
                content = await self._stream_openai_compatible(url, payload, on_thinking, on_content)
            elif "thinking" in message:
                payload.pop("thinking", None)
                content = await self._stream_openai_compatible(url, payload, on_thinking, on_content)
            else:
                raise
        try:
            parsed = json.loads(_strip_json_fence(content))
        except json.JSONDecodeError as exc:
            raise ModelInvalidJSONError(f"Model returned invalid JSON for {schema_name}") from exc
        if not isinstance(parsed, dict):
            raise ModelInvalidJSONError(f"Model returned non-object JSON for {schema_name}")
        return parsed

    def chat_json_streaming_sync(self, **kwargs: Any) -> dict[str, Any]:
        return asyncio.run(self.chat_json_streaming(**kwargs))

    async def _stream_openai_compatible(
        self,
        url: str,
        payload: dict[str, Any],
        on_thinking: Callable[[str], None] | None,
        on_content: Callable[[str], None] | None,
    ) -> str:
        """Read an SSE stream and accumulate `content`. Returns the full content string."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "text/event-stream",
        }
        accumulated = []
        async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds * 4) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code >= 400:
                    body = (await response.aread()).decode(errors="ignore")[:240]
                    raise ModelProviderError(
                        f"Model provider error: HTTP {response.status_code}: {body}"
                    )
                async for raw_line in response.aiter_lines():
                    if not raw_line:
                        continue
                    line = raw_line.strip()
                    if not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if not data_str or data_str == "[DONE]":
                        continue
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    reasoning_chunk = delta.get("reasoning_content")
                    content_chunk = delta.get("content")
                    if reasoning_chunk and on_thinking:
                        try:
                            on_thinking(str(reasoning_chunk))
                        except Exception:  # noqa: BLE001 — never let UI hooks break the stream
                            pass
                    if content_chunk:
                        accumulated.append(str(content_chunk))
                        if on_content:
                            try:
                                on_content(str(content_chunk))
                            except Exception:  # noqa: BLE001
                                pass
        full = "".join(accumulated)
        if not full.strip():
            raise ModelProviderError("Model provider returned empty content")
        return full


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
