"""Tilo Protocol Adapters — bridge external LLM/agent protocols to Tilo AIP.

Each adapter converts protocol-specific output into a Tilo AIP spec, so it can
be rendered with `tilo.view()` or `@adam2go/tilo-react`.

Two patterns:

- **Generate** a full surface (the LLM authors chart/diff/confirmation/…):
    from tilo.adapters.openai import generate_aip_spec
    from tilo.adapters.anthropic_sdk import generate_aip_spec
    from tilo.adapters.langchain import generate_aip_spec

- **Convert** an existing response or protocol message:
    from tilo.adapters.openai import tilo_spec_from_completion
    from tilo.adapters.anthropic_sdk import tilo_spec_from_message
    from tilo.adapters.langchain import TiloCallbackHandler
    from tilo.adapters.mcp import mcp_content_to_blocks, mcp_tool_result_to_spec
    from tilo.adapters.a2a import a2a_task_to_spec
    from tilo.adapters.acp import acp_message_to_spec

The OpenAI / Anthropic / LangChain submodules avoid importing their underlying
SDK at module load, so you can import any adapter without installing every
provider. The protocol adapters below (MCP / A2A / ACP) have no SDK dependency
at all and are re-exported here for convenience.
"""

from tilo.adapters.a2a import a2a_task_to_spec
from tilo.adapters.acp import acp_message_to_spec
from tilo.adapters.agui import agui_events_to_tilo_spec, tilo_spec_to_agui_events
from tilo.adapters.mcp import mcp_content_to_blocks, mcp_tool_result_to_spec

__all__ = [
    "a2a_task_to_spec",
    "acp_message_to_spec",
    "agui_events_to_tilo_spec",
    "tilo_spec_to_agui_events",
    "mcp_content_to_blocks",
    "mcp_tool_result_to_spec",
]
