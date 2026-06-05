"""Tilo high-level generate() API.

The simplest way to turn any LLM call into a full Tilo AIP spec
(with chart, diff, kanban, confirmation, memory_card, etc.).

Usage — auto-detect provider from model name:
    import tilo

    spec = tilo.generate(
        goal="Review this SaaS contract for payment and IP risks.",
        model="gpt-4o",
        api_key="sk-...",
    )
    # spec is a validated ArtifactSpecV1

Usage — OpenAI:
    from tilo.generate import generate_with_openai

    spec = generate_with_openai(
        client=openai.OpenAI(),
        goal="Analyse the Q3 pipeline",
        skill="sales_dashboard",
    )

Usage — Anthropic:
    from tilo.generate import generate_with_anthropic

    spec = generate_with_anthropic(
        client=anthropic.Anthropic(),
        goal="Review this PR for security issues",
        skill="code_review",
        document=pr_diff_text,
    )

Usage — LangChain:
    from tilo.generate import generate_with_langchain

    spec = generate_with_langchain(
        llm=ChatOpenAI(model="gpt-4o"),
        goal="Plan a weekend trip to Tokyo",
    )

Usage — multi-turn (act on a follow-up):
    spec = tilo.generate("Review this contract", model="gpt-4o")
    deeper = tilo.generate_followup(spec, spec.follow_ups[0], model="gpt-4o")
"""

from __future__ import annotations

import os
from typing import Any, Callable

from pydantic import ValidationError

from tilo.prompt import AIPPromptBuilder
from tilo.schemas.artifact import ArtifactSpecV1


# --------------------------------------------------------------------------- #
# Errors & constants                                                           #
# --------------------------------------------------------------------------- #

class TiloGenerationError(RuntimeError):
    """Raised when spec generation fails in a way the caller should handle."""


# Standard env var per provider, used for actionable "no API key" errors.
_PROVIDER_ENV_VARS: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}

# A short instruction appended when asking the model to repair invalid JSON.
_REPAIR_INSTRUCTION = (
    "Your previous response could not be parsed as a valid Tilo AIP JSON object. "
    "Return ONLY the corrected JSON object — no prose, no markdown fences."
)


# --------------------------------------------------------------------------- #
# Shared finalisation: parse -> validate -> repair -> fallback                 #
# --------------------------------------------------------------------------- #

def _finalise(
    raw: str,
    builder: AIPPromptBuilder,
    goal: str,
    *,
    repair_call: Callable[[str], str] | None = None,
    strict: bool = False,
) -> ArtifactSpecV1:
    """Turn raw LLM text into a validated ArtifactSpecV1.

    Order of operations:
      1. parse + validate the first response;
      2. if that fails and a ``repair_call`` is available, ask the model once
         to return corrected JSON, then parse + validate that;
      3. otherwise fall back to a minimal valid spec (or raise if ``strict``).
    """
    spec = _try_build(raw, builder)
    if spec is not None:
        return spec

    if repair_call is not None:
        try:
            repaired = repair_call(_REPAIR_INSTRUCTION)
            spec = _try_build(repaired, builder)
            if spec is not None:
                return spec
        except Exception:  # noqa: BLE001 — repair is best-effort
            pass

    if strict:
        raise TiloGenerationError(
            "The model did not return a valid AIP spec. Raw output:\n"
            f"{raw[:500]}{'…' if len(raw) > 500 else ''}"
        )
    return ArtifactSpecV1.model_validate(_fallback_spec(goal))


def _try_build(raw: str, builder: AIPPromptBuilder) -> ArtifactSpecV1 | None:
    """Parse + validate; return None on any failure (parse or schema)."""
    spec_dict = builder.parse(raw)
    if spec_dict is None:
        return None
    try:
        return ArtifactSpecV1.model_validate(spec_dict)
    except ValidationError:
        return None


# --------------------------------------------------------------------------- #
# Provider-specific generate functions                                         #
# --------------------------------------------------------------------------- #

def generate_with_openai(
    client: Any,
    goal: str,
    *,
    model: str = "gpt-4o",
    skill: str | None = "auto",
    document: str | None = None,
    memories: list[str] | None = None,
    language: str | None = None,
    temperature: float = 0.3,
    repair: bool = True,
    strict: bool = False,
) -> ArtifactSpecV1:
    """Generate a full Tilo AIP spec using an OpenAI client.

    Args:
        client:      An ``openai.OpenAI()`` instance.
        goal:        What the artifact should address.
        model:       OpenAI model name (default: "gpt-4o").
        skill:       Skill hint ("contract_review", …) or "auto" to detect.
        document:    Optional document text (contract, PR diff, etc.).
        memories:    Optional recalled user preferences.
        language:    "en" or "zh" to force output language.
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).
        repair:      On invalid JSON, ask the model once to fix it (default True).
        strict:      Raise ``TiloGenerationError`` instead of returning a
                     fallback spec when generation fails.

    Returns:
        A validated ``ArtifactSpecV1`` instance.
    """
    builder = AIPPromptBuilder(
        goal=goal, skill=skill, document=document,
        memories=memories, language=language,
    )

    def _invoke(extra_user: str | None = None) -> str:
        messages = builder.messages_openai()
        if extra_user:
            messages = [*messages, {"role": "user", "content": extra_user}]
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    raw = _invoke()
    return _finalise(raw, builder, goal, repair_call=_invoke if repair else None, strict=strict)


def generate_with_anthropic(
    client: Any,
    goal: str,
    *,
    model: str = "claude-opus-4-8",
    skill: str | None = "auto",
    document: str | None = None,
    memories: list[str] | None = None,
    language: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.3,
    repair: bool = True,
    strict: bool = False,
) -> ArtifactSpecV1:
    """Generate a full Tilo AIP spec using an Anthropic client.

    Args:
        client:      An ``anthropic.Anthropic()`` instance.
        goal:        What the artifact should address.
        model:       Anthropic model name (default: "claude-opus-4-8").
        skill:       Skill hint or "auto" to detect.
        document:    Optional document text.
        memories:    Optional recalled user preferences.
        language:    "en" or "zh" to force output language.
        max_tokens:  Max tokens for the response (default: 4096).
        temperature: Sampling temperature (0.0–1.0).
        repair:      On invalid JSON, ask the model once to fix it (default True).
        strict:      Raise instead of returning a fallback spec on failure.

    Returns:
        A validated ``ArtifactSpecV1`` instance.
    """
    builder = AIPPromptBuilder(
        goal=goal, skill=skill, document=document,
        memories=memories, language=language,
    )
    base = builder.messages_anthropic()

    def _invoke(extra_user: str | None = None) -> str:
        messages = list(base["messages"])
        if extra_user:
            messages = [*messages, {"role": "user", "content": extra_user}]
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=base["system"],
            messages=messages,
        )
        text = ""
        for block in response.content:
            if getattr(block, "type", None) == "text":
                text += getattr(block, "text", "")
        return text

    raw = _invoke()
    return _finalise(raw, builder, goal, repair_call=_invoke if repair else None, strict=strict)


def generate_with_langchain(
    llm: Any,
    goal: str,
    *,
    skill: str | None = "auto",
    document: str | None = None,
    memories: list[str] | None = None,
    language: str | None = None,
    repair: bool = True,
    strict: bool = False,
) -> ArtifactSpecV1:
    """Generate a full Tilo AIP spec using any LangChain chat model.

    Args:
        llm:       Any LangChain chat model (ChatOpenAI, ChatAnthropic, etc.).
        goal:      What the artifact should address.
        skill:     Skill hint or "auto" to detect.
        document:  Optional document text.
        memories:  Optional recalled user preferences.
        language:  "en" or "zh" to force output language.
        repair:    On invalid JSON, ask the model once to fix it (default True).
        strict:    Raise instead of returning a fallback spec on failure.

    Returns:
        A validated ``ArtifactSpecV1`` instance.

    Note:
        Control temperature on the LangChain model itself
        (e.g. ``ChatOpenAI(model="gpt-4o", temperature=0.3)``).
    """
    try:
        from langchain_core.messages import HumanMessage
        from langchain_core.output_parsers import StrOutputParser
    except ImportError:
        raise ImportError("pip install langchain-core to use generate_with_langchain()")

    builder = AIPPromptBuilder(
        goal=goal, skill=skill, document=document,
        memories=memories, language=language,
    )
    prompt_template = builder.messages_langchain()
    base_messages = prompt_template.format_messages()
    parser = StrOutputParser()

    def _invoke(extra_user: str | None = None) -> str:
        messages = list(base_messages)
        if extra_user:
            messages = [*messages, HumanMessage(content=extra_user)]
        return parser.invoke(llm.invoke(messages))

    raw = _invoke()
    return _finalise(raw, builder, goal, repair_call=_invoke if repair else None, strict=strict)


# --------------------------------------------------------------------------- #
# Top-level generate() — auto-detects provider                                #
# --------------------------------------------------------------------------- #

def generate(
    goal: str,
    *,
    model: str | None = None,
    api_key: str | None = None,
    provider: str | None = None,
    skill: str | None = "auto",
    document: str | None = None,
    memories: list[str] | None = None,
    language: str | None = None,
    temperature: float = 0.3,
    repair: bool = True,
    strict: bool = False,
) -> ArtifactSpecV1:
    """Generate a full Tilo AIP spec from any goal string.

    Automatically selects the LLM provider from the model name or
    ``provider`` argument. Requires the corresponding SDK to be installed.

    Args:
        goal:        What the artifact should address.
        model:       Model name. Provider is auto-detected:
                     - "gpt-*" / "o1-*" / "o3-*"  → OpenAI
                     - "claude-*"                   → Anthropic
                     Defaults to "gpt-4o-mini" if not set.
        api_key:     API key. Falls back to the provider's standard env var.
        provider:    Force provider: "openai" or "anthropic".
        skill:       Skill hint or "auto" to detect from goal.
        document:    Optional document text.
        memories:    Optional recalled user preferences.
        language:    "en" or "zh" to force output language.
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).
        repair:      On invalid JSON, ask the model once to fix it.
        strict:      Raise ``TiloGenerationError`` on failure instead of a
                     fallback spec.

    Returns:
        A validated ``ArtifactSpecV1`` with all block types available
        (chart, diff, timeline, confirmation, memory_card, etc.).

    Examples:
        import tilo
        spec = tilo.generate("Review this contract", model="gpt-4o")
        spec = tilo.generate("Plan a Tokyo trip", model="claude-opus-4-8")
    """
    if model is None:
        model = "gpt-4o-mini"

    resolved_provider = provider or _detect_provider(model)
    common: dict[str, Any] = dict(
        goal=goal, skill=skill, document=document,
        memories=memories, language=language,
        temperature=temperature, repair=repair, strict=strict,
    )

    if resolved_provider == "openai":
        client = _make_openai_client(api_key)
        return generate_with_openai(client, model=model, **common)

    if resolved_provider == "anthropic":
        client = _make_anthropic_client(api_key)
        return generate_with_anthropic(client, model=model, **common)

    raise ValueError(
        f"Cannot auto-detect a provider for model '{model}'. "
        "Pass provider='openai' or provider='anthropic' explicitly, or use "
        "generate_with_openai() / generate_with_anthropic() / generate_with_langchain()."
    )


def generate_followup(
    previous: ArtifactSpecV1,
    followup: str,
    *,
    model: str | None = None,
    api_key: str | None = None,
    provider: str | None = None,
    temperature: float = 0.3,
    repair: bool = True,
    strict: bool = False,
) -> ArtifactSpecV1:
    """Generate a follow-up surface that builds on a previous one.

    Use this to act on a spec's ``follow_ups`` — the new surface is generated
    with the previous surface as context, so the model can deepen, compare, or
    extend the prior result.

    Args:
        previous:  The spec to build on (e.g. a prior ``generate()`` result).
        followup:  The follow-up goal (often one of ``previous.follow_ups``).
        model:     Model name (defaults to the same family heuristic as generate).
        api_key:   API key, or rely on the provider env var.
        provider:  Force provider.
        temperature / repair / strict: as in ``generate()``.

    Returns:
        A new validated ``ArtifactSpecV1``.

    Example:
        spec = tilo.generate("Review this contract", model="gpt-4o")
        deeper = tilo.generate_followup(spec, spec.follow_ups[0], model="gpt-4o")
    """
    prior_summary = _summarise_spec(previous)
    goal = (
        f"Building on a previous result titled \"{previous.title}\", address this "
        f"follow-up: {followup}"
    )
    return generate(
        goal,
        model=model,
        api_key=api_key,
        provider=provider,
        skill="auto",
        document=prior_summary,
        temperature=temperature,
        repair=repair,
        strict=strict,
    )


# --------------------------------------------------------------------------- #
# Client construction with actionable errors                                   #
# --------------------------------------------------------------------------- #

def _make_openai_client(api_key: str | None) -> Any:
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            'OpenAI SDK not installed. Run: pip install "tilo[openai]"'
        )
    _require_key("openai", api_key)
    return OpenAI(api_key=api_key) if api_key else OpenAI()


def _make_anthropic_client(api_key: str | None) -> Any:
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            'Anthropic SDK not installed. Run: pip install "tilo[anthropic]"'
        )
    _require_key("anthropic", api_key)
    return anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()


def _require_key(provider: str, api_key: str | None) -> None:
    """Raise an actionable error if no API key is available."""
    if api_key:
        return
    env_var = _PROVIDER_ENV_VARS.get(provider, "API_KEY")
    if not os.environ.get(env_var):
        raise TiloGenerationError(
            f"No API key for {provider}. Set the {env_var} environment variable, "
            f"or pass api_key=... to generate(). "
            f"No key at all? Run `tilo demo` to see a sample surface."
        )


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

def _detect_provider(model: str) -> str | None:
    m = model.lower()
    if m.startswith(("gpt-", "o1-", "o3-", "text-", "ft:gpt")):
        return "openai"
    if m.startswith("claude-"):
        return "anthropic"
    return None


def _summarise_spec(spec: ArtifactSpecV1, limit: int = 1500) -> str:
    """Produce a compact text summary of a spec to feed back as context."""
    lines = [f"# {spec.title}"]
    for block in spec.blocks:
        props = block.props or {}
        snippet = (
            props.get("content")
            or props.get("text")
            or props.get("description")
            or props.get("summary")
            or block.title
            or ""
        )
        lines.append(f"- [{block.type}] {str(snippet)[:120]}")
    text = "\n".join(lines)
    return text[:limit] + ("…" if len(text) > limit else "")


def _fallback_spec(goal: str) -> dict[str, Any]:
    """Return a minimal valid spec when LLM parsing fails."""
    words = goal.split()[:8]
    title = " ".join(words) + ("…" if len(goal.split()) > 8 else "")
    return {
        "version": "tilo/aip/v1",
        "title": title,
        "status": "ready",
        "blocks": [
            {
                "id": "b_main",
                "type": "markdown",
                "title": "Result",
                "props": {"content": f"Processing: {goal}"},
            },
            {
                "id": "b_mem",
                "type": "memory_card",
                "title": "Note",
                "props": {"content": "No preferences captured yet.", "confidence": 0.5},
            },
        ],
        "views": [{"id": "main", "label": "Result", "block_ids": ["b_main", "b_mem"]}],
        "actions": [],
        "follow_ups": [],
        "memory_refs": [],
        "provenance": [{"type": "aip_fallback", "id": "tilo.generate.fallback"}],
    }
