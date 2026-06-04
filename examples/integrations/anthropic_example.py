"""Anthropic → Tilo AIP — complete working example.

Shows three patterns for converting Anthropic responses into renderable Tilo surfaces:
  1. Direct conversion (non-streaming)
  2. Managed streaming handler
  3. Tool use → tool_preview blocks

Requirements:
    pip install tilo anthropic

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python examples/integrations/anthropic_example.py
"""

from __future__ import annotations

import os

from tilo.adapters.anthropic_sdk import TiloMessageHandler, tilo_spec_from_message
from tilo.schemas.artifact import ArtifactSpecV1


def _print_spec(spec: dict, label: str) -> None:
    validated = ArtifactSpecV1.model_validate(spec)
    print(f"\n{'─' * 50}")
    print(f"[{label}]  {validated.title}")
    print(f"  Blocks: {[b.type for b in validated.blocks]}")
    for block in validated.blocks[:3]:
        preview = str(block.props or {})[:80]
        print(f"  · {block.type:16s} {preview}")


def example_1_direct(client) -> None:
    """Non-streaming: convert a Message response directly."""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": "List 3 key risks in a SaaS contract renewal."}],
    )
    spec = tilo_spec_from_message(response, title="Contract Risks")
    _print_spec(spec, "Direct conversion")


def example_2_streaming(client) -> None:
    """Managed streaming: accumulate via text_stream."""
    handler = TiloMessageHandler(title="Q3 Analysis", model="claude-haiku-4-5-20251001")
    with client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=150,
        messages=[{"role": "user", "content": "Summarise Q3 sales in 2 sentences."}],
    ) as stream:
        for text in stream.text_stream:
            handler.on_text(text)
    spec = handler.to_spec()
    _print_spec(spec, "Managed stream")


def example_3_structured_json(client) -> None:
    """Ask Claude to return JSON — auto-converts to metric/table blocks."""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=150,
        messages=[{
            "role": "user",
            "content": (
                "Return ONLY a JSON object with: revenue_usd (number), "
                "deals_closed (number), top_region (string), churn_rate (string like '1.8%')."
            ),
        }],
    )
    spec = tilo_spec_from_message(response, title="Q3 Metrics")
    _print_spec(spec, "JSON → metric blocks")


def example_4_tool_use(client) -> None:
    """Tool use → tool_preview blocks."""
    tools = [{
        "name": "get_contract_clause",
        "description": "Retrieve a specific clause from the contract",
        "input_schema": {
            "type": "object",
            "properties": {"clause_id": {"type": "string", "description": "Clause identifier"}},
            "required": ["clause_id"],
        },
    }]
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        tools=tools,
        messages=[{"role": "user", "content": "Get clause 8.2 from the contract."}],
    )
    spec = tilo_spec_from_message(response, title="Tool Preview")
    _print_spec(spec, "Tool use → tool_preview blocks")


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY and re-run.")
        print("\nExample spec (deterministic, no API key):")
        from tilo.schemas.artifact import ArtifactSpecV1
        spec = {
            "version": "tilo/aip/v1",
            "title": "Claude Summary",
            "status": "ready",
            "blocks": [
                {"id": "h", "type": "heading", "props": {"text": "Q3 Analysis", "severity": "info"}},
                {"id": "t", "type": "markdown", "props": {"content": "Strong performance across all regions."}},
            ],
            "views": [{"id": "v", "label": "Summary", "block_ids": ["h", "t"]}],
            "actions": [],
            "follow_ups": ["What drove the growth?"],
        }
        _print_spec(spec, "Deterministic demo")
        return

    try:
        import anthropic
    except ImportError:
        print("Install anthropic: pip install anthropic")
        return

    client = anthropic.Anthropic(api_key=api_key)
    print("Running Anthropic → Tilo AIP examples...\n")

    example_1_direct(client)
    example_2_streaming(client)
    example_3_structured_json(client)
    example_4_tool_use(client)

    print("\n✓ All examples complete.")
    print("  Render any spec dict with @adam2go/tilo-react:")
    print("  import { renderArtifactBlock } from '@adam2go/tilo-react'")


if __name__ == "__main__":
    main()
