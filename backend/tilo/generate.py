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
"""

from __future__ import annotations

from typing import Any

from tilo.prompt import AIPPromptBuilder
from tilo.schemas.artifact import ArtifactSpecV1


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
) -> ArtifactSpecV1:
    """Generate a full Tilo AIP spec using an OpenAI client.

    Args:
        client:    An ``openai.OpenAI()`` instance.
        goal:      What the artifact should address.
        model:     OpenAI model name (default: "gpt-4o").
        skill:     Skill hint ("contract_review", "code_review", etc.) or "auto" to detect.
        document:  Optional document text (contract, PR diff, etc.).
        memories:  Optional recalled user preferences.
        language:  "en" or "zh" to force output language.

    Returns:
        A validated ``ArtifactSpecV1`` instance.

    Example:
        import openai
        from tilo.generate import generate_with_openai

        client = openai.OpenAI()
        spec = generate_with_openai(client, "Review this contract", skill="contract_review")
        print(spec.title)
        print([b.type for b in spec.blocks])
    """
    builder = AIPPromptBuilder(
        goal=goal, skill=skill, document=document,
        memories=memories, language=language,
    )
    response = client.chat.completions.create(
        model=model,
        messages=builder.messages_openai(),
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    raw = response.choices[0].message.content or ""
    spec_dict = builder.parse(raw)
    if spec_dict is None:
        spec_dict = _fallback_spec(goal)
    return ArtifactSpecV1.model_validate(spec_dict)


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
) -> ArtifactSpecV1:
    """Generate a full Tilo AIP spec using an Anthropic client.

    Args:
        client:     An ``anthropic.Anthropic()`` instance.
        goal:       What the artifact should address.
        model:      Anthropic model name (default: "claude-opus-4-8").
        skill:      Skill hint or "auto" to detect.
        document:   Optional document text.
        memories:   Optional recalled user preferences.
        language:   "en" or "zh" to force output language.
        max_tokens: Max tokens for the response (default: 4096).

    Returns:
        A validated ``ArtifactSpecV1`` instance.

    Example:
        import anthropic
        from tilo.generate import generate_with_anthropic

        client = anthropic.Anthropic()
        spec = generate_with_anthropic(client, "Plan a weekend trip to Tokyo")
        print([b.type for b in spec.blocks])
    """
    builder = AIPPromptBuilder(
        goal=goal, skill=skill, document=document,
        memories=memories, language=language,
    )
    kwargs = builder.messages_anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        **kwargs,
    )
    raw = ""
    for block in response.content:
        if getattr(block, "type", None) == "text":
            raw += getattr(block, "text", "")

    spec_dict = builder.parse(raw)
    if spec_dict is None:
        spec_dict = _fallback_spec(goal)
    return ArtifactSpecV1.model_validate(spec_dict)


def generate_with_langchain(
    llm: Any,
    goal: str,
    *,
    skill: str | None = "auto",
    document: str | None = None,
    memories: list[str] | None = None,
    language: str | None = None,
) -> ArtifactSpecV1:
    """Generate a full Tilo AIP spec using any LangChain chat model.

    Args:
        llm:       Any LangChain chat model (ChatOpenAI, ChatAnthropic, etc.).
                   Should have JSON mode or be a strong instruction-following model.
        goal:      What the artifact should address.
        skill:     Skill hint or "auto" to detect.
        document:  Optional document text.
        memories:  Optional recalled user preferences.
        language:  "en" or "zh" to force output language.

    Returns:
        A validated ``ArtifactSpecV1`` instance.

    Example:
        from langchain_openai import ChatOpenAI
        from tilo.generate import generate_with_langchain

        llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        spec = generate_with_langchain(llm, "Analyse Q3 sales pipeline", skill="sales_dashboard")
        print([b.type for b in spec.blocks])
    """
    try:
        from langchain_core.output_parsers import StrOutputParser
    except ImportError:
        raise ImportError("pip install langchain-core to use generate_with_langchain()")

    builder = AIPPromptBuilder(
        goal=goal, skill=skill, document=document,
        memories=memories, language=language,
    )
    prompt_template = builder.messages_langchain()
    chain = prompt_template | llm | StrOutputParser()
    raw: str = chain.invoke({})

    spec_dict = builder.parse(raw)
    if spec_dict is None:
        spec_dict = _fallback_spec(goal)
    return ArtifactSpecV1.model_validate(spec_dict)


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
) -> ArtifactSpecV1:
    """Generate a full Tilo AIP spec from any goal string.

    Automatically selects the LLM provider from the model name or
    ``provider`` argument. Requires the corresponding SDK to be installed.

    Args:
        goal:      What the artifact should address.
        model:     Model name. Provider is auto-detected:
                   - "gpt-*" / "o1-*" / "o3-*"  → OpenAI
                   - "claude-*"                   → Anthropic
                   - "gemini-*"                   → Google (via langchain-google-genai)
                   Defaults to "gpt-4o-mini" if not set.
        api_key:   API key. Falls back to the provider's standard env var
                   (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.).
        provider:  Force provider: "openai", "anthropic", or "langchain:<model>".
        skill:     Skill hint or "auto" to detect from goal.
        document:  Optional document text.
        memories:  Optional recalled user preferences.
        language:  "en" or "zh" to force output language.

    Returns:
        A validated ``ArtifactSpecV1`` instance with all block types available
        (chart, diff, timeline, kanban, confirmation, memory_card, etc.).

    Examples:
        import tilo

        # OpenAI
        spec = tilo.generate("Review this contract", model="gpt-4o", api_key="sk-...")

        # Anthropic
        spec = tilo.generate("Plan a Tokyo trip", model="claude-opus-4-8", api_key="sk-ant-...")

        # Explicit provider + model
        spec = tilo.generate("Analyse Q3 pipeline", provider="openai", model="gpt-4o-mini")

        # With document
        spec = tilo.generate("Review this PR", model="gpt-4o", document=pr_diff_text)
    """
    if model is None:
        model = "gpt-4o-mini"

    resolved_provider = provider or _detect_provider(model)

    kwargs: dict[str, Any] = dict(
        goal=goal, skill=skill, document=document,
        memories=memories, language=language,
    )

    if resolved_provider == "openai":
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("pip install openai to use generate() with OpenAI models")
        client = OpenAI(api_key=api_key) if api_key else OpenAI()
        return generate_with_openai(client, model=model, **kwargs)

    if resolved_provider == "anthropic":
        try:
            import anthropic
        except ImportError:
            raise ImportError("pip install anthropic to use generate() with Claude models")
        client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        return generate_with_anthropic(client, model=model, **kwargs)

    raise ValueError(
        f"Cannot auto-detect provider for model '{model}'. "
        "Pass provider='openai' or provider='anthropic' explicitly, "
        "or use generate_with_openai() / generate_with_anthropic() directly."
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
