"""LangChain → Tilo AIP — complete working example.

Shows how to add Tilo rendering to any LangChain chain with one callback.

Requirements:
    pip install tilo langchain-openai langchain-core

Usage:
    export OPENAI_API_KEY=sk-...
    python examples/integrations/langchain_example.py
"""

from __future__ import annotations

import os

from tilo.adapters.langchain import TiloCallbackHandler, langchain_result_to_spec
from tilo.schemas.artifact import ArtifactSpecV1


def _print_spec(spec: dict, label: str) -> None:
    validated = ArtifactSpecV1.model_validate(spec)
    print(f"\n{'─' * 50}")
    print(f"[{label}]  {validated.title}")
    for block in validated.blocks[:4]:
        preview = str(block.props or {})[:80]
        print(f"  · {block.type:16s} {preview}")


def example_1_callback_handler() -> None:
    """Add TiloCallbackHandler to any LangChain chain — one line."""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage

    handler = TiloCallbackHandler(title="Contract Analysis")
    llm = ChatOpenAI(model="gpt-4o-mini", max_tokens=200)

    llm.invoke(
        [HumanMessage(content="List 3 contract risks in bullet points.")],
        config={"callbacks": [handler]},
    )
    spec = handler.to_spec()
    _print_spec(spec, "Callback handler")


def example_2_chain() -> None:
    """Full LangChain chain with Tilo output."""
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    handler = TiloCallbackHandler(title="Sales Briefing")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a concise sales analyst."),
        ("human", "{topic}"),
    ])
    chain = prompt | ChatOpenAI(model="gpt-4o-mini", max_tokens=150) | StrOutputParser()
    output = chain.invoke(
        {"topic": "Q3 pipeline summary"},
        config={"callbacks": [handler]},
    )

    # Option A: use the callback handler (captures LLM output)
    spec_a = handler.to_spec()
    _print_spec(spec_a, "Chain (callback handler)")

    # Option B: convert chain output directly
    spec_b = langchain_result_to_spec("Sales Briefing", {"output": output})
    _print_spec(spec_b, "Chain (direct conversion)")


def example_3_agent_with_tools() -> None:
    """LangChain agent with tools — tool calls appear as tool_preview blocks."""
    from langchain_openai import ChatOpenAI
    from langchain_core.tools import tool
    from langchain.agents import AgentExecutor, create_openai_tools_agent
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

    @tool
    def search_contracts(query: str) -> str:
        """Search the contract database."""
        return f"Found 3 contracts matching '{query}': SaaS-001, SaaS-002, SaaS-003"

    handler = TiloCallbackHandler(title="Contract Search")
    llm = ChatOpenAI(model="gpt-4o-mini", max_tokens=200)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a contract assistant. Use tools to find contracts."),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm, [search_contracts], prompt)
    executor = AgentExecutor(agent=agent, tools=[search_contracts], verbose=False)
    executor.invoke(
        {"input": "Find SaaS contracts about data processing"},
        config={"callbacks": [handler]},
    )
    spec = handler.to_spec()
    _print_spec(spec, "Agent with tools")


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Set OPENAI_API_KEY and re-run.")
        print("\nExample (no API key — showing TiloCallbackHandler interface):")
        print("  from tilo.adapters.langchain import TiloCallbackHandler")
        print("  handler = TiloCallbackHandler(title='My Chain')")
        print("  chain.invoke(input, config={'callbacks': [handler]})")
        print("  spec = handler.to_spec()  # → Tilo AIP v1 dict")
        return

    try:
        import langchain_openai  # noqa: F401
    except ImportError:
        print("Install: pip install langchain-openai langchain-core")
        return

    print("Running LangChain → Tilo AIP examples...\n")

    example_1_callback_handler()
    example_2_chain()

    try:
        from langchain.agents import AgentExecutor  # noqa: F401
        example_3_agent_with_tools()
    except ImportError:
        print("\n(Skipping agent example — pip install langchain to enable)")

    print("\n✓ All examples complete.")


if __name__ == "__main__":
    main()
