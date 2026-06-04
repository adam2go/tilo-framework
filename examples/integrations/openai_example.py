"""OpenAI → Tilo AIP — complete working example.

Shows three patterns for converting OpenAI responses into renderable Tilo surfaces:
  1. Direct conversion (non-streaming)
  2. Streaming handler
  3. Structured JSON output → typed blocks

Requirements:
    pip install tilo openai

Usage:
    export OPENAI_API_KEY=sk-...
    python examples/integrations/openai_example.py
"""

from __future__ import annotations

import json
import os

# ── 1. Import Tilo adapter ──────────────────────────────────────────────────

from tilo.adapters.openai import TiloCompletionHandler, tilo_spec_from_completion
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
    """Non-streaming: convert a ChatCompletion response in one call."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a concise business analyst."},
            {"role": "user", "content": "Give me 3 key risks for a SaaS contract renewal."},
        ],
        max_tokens=300,
    )
    spec = tilo_spec_from_completion(response, title="Contract Risks")
    _print_spec(spec, "Direct conversion")


def example_2_streaming(client) -> None:
    """Streaming: accumulate chunks, then build spec."""
    handler = TiloCompletionHandler(title="Q3 Analysis")
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Summarise Q3 sales performance in 2 sentences."}],
        max_tokens=150,
        stream=True,
    )
    for chunk in stream:
        handler.on_chunk(chunk)
    spec = handler.to_spec()
    _print_spec(spec, "Streaming")


def example_3_structured_output(client) -> None:
    """Structured JSON output → metric/table blocks automatically."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": (
                "Return ONLY JSON with keys: revenue_usd (number), "
                "deals_closed (number), churn_rate (string like '2.1%'), "
                "top_region (string)."
            ),
        }],
        response_format={"type": "json_object"},
        max_tokens=100,
    )
    spec = tilo_spec_from_completion(response, title="Q3 Metrics")
    _print_spec(spec, "Structured JSON → metric blocks")


def example_4_tool_calls(client) -> None:
    """Tool calls → tool_preview blocks."""
    tools = [{
        "type": "function",
        "function": {
            "name": "get_contract_clause",
            "description": "Retrieve a specific clause from the contract",
            "parameters": {
                "type": "object",
                "properties": {"clause_id": {"type": "string"}},
                "required": ["clause_id"],
            },
        },
    }]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Get clause 8.2 from the contract."}],
        tools=tools,
        tool_choice="auto",
        max_tokens=100,
    )
    spec = tilo_spec_from_completion(response, title="Tool Preview")
    _print_spec(spec, "Tool calls → tool_preview blocks")


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Set OPENAI_API_KEY and re-run.")
        print("\nExample spec (deterministic, no API key):")
        spec = {
            "version": "tilo/aip/v1",
            "title": "Demo Surface",
            "status": "ready",
            "blocks": [
                {"id": "h", "type": "heading", "props": {"text": "Q3 Results", "severity": "info"}},
                {"id": "m", "type": "metric", "props": {"label": "Revenue", "value": "$1.2M"}},
                {"id": "t", "type": "markdown", "props": {"content": "Strong growth in APAC."}},
            ],
            "views": [{"id": "v", "label": "Summary", "block_ids": ["h", "m", "t"]}],
            "actions": [],
            "follow_ups": [],
        }
        _print_spec(spec, "Deterministic demo")
        return

    try:
        from openai import OpenAI
    except ImportError:
        print("Install openai: pip install openai")
        return

    client = OpenAI(api_key=api_key)
    print("Running OpenAI → Tilo AIP examples...\n")

    example_1_direct(client)
    example_2_streaming(client)
    example_3_structured_output(client)
    example_4_tool_calls(client)

    print("\n✓ All examples complete.")
    print("  Render any spec dict with @adam2go/tilo-react:")
    print("  import { renderArtifactBlock } from '@adam2go/tilo-react'")


if __name__ == "__main__":
    main()
