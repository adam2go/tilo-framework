"""Tilo — AI-native product runtime framework.

Quick start:
    pip install tilo openai   # or: anthropic / langchain-openai
    tilo init myapp && cd myapp && tilo serve

Generate a full interactive AIP spec from any LLM in one line:
    import tilo

    spec = tilo.generate(
        "Review this SaaS contract for payment and IP risks.",
        model="gpt-4o",
        api_key="sk-...",
    )
    # spec.blocks → chart, diff, table, confirmation, memory_card, ...
    # Render with: npm install @adam2go/tilo-react

Provider-specific entry points:
    from tilo.generate import generate_with_openai, generate_with_anthropic, generate_with_langchain

Adapters (convert existing LLM responses):
    from tilo.adapters.openai        import tilo_spec_from_completion
    from tilo.adapters.anthropic_sdk import tilo_spec_from_message
    from tilo.adapters.langchain     import TiloCallbackHandler
    from tilo.adapters.mcp           import mcp_content_to_blocks

Prompt builder (bring-your-own LLM client):
    from tilo.prompt import AIPPromptBuilder
    builder = AIPPromptBuilder(goal="...", skill="contract_review")
    system  = builder.system_prompt()
    user    = builder.user_prompt()
    spec    = builder.parse(llm_json_response)
"""

from tilo.generate import (
    TiloGenerationError,
    generate,
    generate_followup,
    generate_with_anthropic,
    generate_with_langchain,
    generate_with_openai,
)
from tilo.prompt import AIPPromptBuilder, BUILTIN_SKILLS, detect_skill
from tilo.viewer import load_spec, notebook, save_html, save_spec, to_html, view

__all__ = [
    # Generation
    "generate",
    "generate_followup",
    "generate_with_openai",
    "generate_with_anthropic",
    "generate_with_langchain",
    "TiloGenerationError",
    # Prompt builder
    "AIPPromptBuilder",
    "detect_skill",
    "BUILTIN_SKILLS",
    # Viewer
    "view",
    "to_html",
    "save_html",
    "save_spec",
    "load_spec",
    "notebook",
]
