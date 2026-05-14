"""LangChain → Tilo AIP adapter (stub).

Provides a callback handler that captures LangChain chain output
and converts it into a Tilo AIP spec.

Usage:
    from tilo.adapters.langchain import TiloCallbackHandler

    chain.invoke(input, config={"callbacks": [TiloCallbackHandler(run_id="...")]})

Status: Interface only. Implementation planned for M5+.
"""

from typing import Any


class TiloCallbackHandler:
    """LangChain callback that captures output as Tilo AIP blocks.

    This is a stub interface. Full implementation will:
    - Capture AIMessage → markdown block
    - Capture ToolMessage → tool_preview block
    - Capture structured output → mapped block types
    - Build a complete spec on chain end
    """

    def __init__(self, run_id: str | None = None) -> None:
        self.run_id = run_id
        self.blocks: list[dict[str, Any]] = []

    def on_chain_end(self, outputs: dict[str, Any], **kwargs: Any) -> None:
        """Called when a chain finishes. Stub — does nothing yet."""
        pass

    def to_spec(self) -> dict[str, Any]:
        """Convert captured output to a Tilo AIP spec. Stub."""
        return {
            "version": "tilo/aip/v1",
            "title": "LangChain Result",
            "status": "ready",
            "blocks": self.blocks or [
                {"id": "placeholder", "type": "markdown", "props": {"content": "No output captured."}},
            ],
            "views": [],
            "actions": [],
            "provenance": [],
            "memory_refs": [],
            "follow_ups": [],
        }
