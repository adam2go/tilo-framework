"""AG-UI best practice #2 — render an AG-UI agent's output as a Tilo surface.

Pattern: you already have an AG-UI agent (LangGraph, CrewAI, Mastra, …) that
streams text + tool calls. Aggregate that event stream into ONE structured
Tilo surface — a clean artifact you can render anywhere (no CopilotKit needed).

Runs on the lean install (`pip install tilo`).

    python examples/integrations/agui/consume_stream.py
"""

from __future__ import annotations

import tilo
from tilo.adapters.agui import agui_events_to_tilo_spec


# A realistic AG-UI event stream from an agent that searched, then summarised.
SAMPLE_STREAM = [
    {"type": "RUN_STARTED", "threadId": "t1", "runId": "r1"},
    {"type": "TEXT_MESSAGE_START", "messageId": "m1", "role": "assistant"},
    {"type": "TEXT_MESSAGE_CONTENT", "messageId": "m1", "delta": "I reviewed the contract. "},
    {"type": "TEXT_MESSAGE_CONTENT", "messageId": "m1", "delta": "Two clauses need attention before signing."},
    {"type": "TEXT_MESSAGE_END", "messageId": "m1"},
    {"type": "TOOL_CALL_START", "toolCallId": "tc1", "toolCallName": "lookup_clause"},
    {"type": "TOOL_CALL_ARGS", "toolCallId": "tc1", "delta": '{"section": "8.2"}'},
    {"type": "TOOL_CALL_END", "toolCallId": "tc1"},
    {"type": "TOOL_CALL_RESULT", "toolCallId": "tc1",
     "content": "8.2 Liability: unlimited. Recommend cap at 12 months' fees."},
    {"type": "RUN_FINISHED", "threadId": "t1", "runId": "r1"},
]


def main() -> None:
    spec = agui_events_to_tilo_spec(SAMPLE_STREAM, title="Contract Review (from AG-UI agent)")

    print(f"Aggregated {len(SAMPLE_STREAM)} AG-UI events into a Tilo surface:")
    print(f"  Title:  {spec['title']}")
    print(f"  Blocks: {[b['type'] for b in spec['blocks']]}")

    tilo.save_html(spec, "/tmp/agui_consumed_surface.html")
    print("\nSaved a standalone render to /tmp/agui_consumed_surface.html")
    print("(use tilo.view(spec) to open it in your browser, or tilo.notebook(spec) in Jupyter)")


if __name__ == "__main__":
    main()
