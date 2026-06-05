"""Anthropic → Tilo AIP adapter.

Converts Anthropic Messages API responses into Tilo AIP specs.
No hard dependency on the anthropic package at import time — duck-typed.

Usage (direct conversion):
    import anthropic
    from tilo.adapters.anthropic_sdk import tilo_spec_from_message

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Summarise the Q3 results"}],
    )
    spec = tilo_spec_from_message(response)          # → Tilo AIP v1 dict

Usage (streaming handler):
    from tilo.adapters.anthropic_sdk import TiloMessageHandler

    handler = TiloMessageHandler(title="Q3 Report")
    with client.messages.stream(...) as stream:
        for text in stream.text_stream:
            handler.on_text(text)
    spec = handler.to_spec()

Mapping:
    text block        → markdown (or metric/table if JSON-parseable)
    tool_use block    → tool_preview (name + JSON input as formatted output)
"""

from __future__ import annotations

import json
import uuid
from typing import Any


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

def _new_id(prefix: str = "ant") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _text_block(text: str, block_id: str | None = None) -> dict[str, Any]:
    return {
        "id": block_id or _new_id("ant_text"),
        "type": "markdown",
        "title": None,
        "props": {"content": text.strip()},
    }


def _tool_use_block(
    name: str,
    input_data: dict[str, Any] | str,
    block_id: str | None = None,
) -> dict[str, Any]:
    if isinstance(input_data, dict):
        output = json.dumps(input_data, indent=2, ensure_ascii=False)
    else:
        output = str(input_data)
    return {
        "id": block_id or _new_id("ant_tool"),
        "type": "tool_preview",
        "title": name,
        "props": {
            "tool_name": name,
            "status": "pending",
            "output": output,
        },
    }


def _structured_blocks(data: Any, prefix: str = "ant_struct") -> list[dict[str, Any]]:
    if isinstance(data, dict):
        is_metrics = (
            len(data) <= 8
            and all(
                isinstance(v, (int, float))
                or (isinstance(v, str) and len(v) < 40)
                for v in data.values()
            )
        )
        if is_metrics:
            return [
                {
                    "id": f"{prefix}_{i}",
                    "type": "metric",
                    "title": k.replace("_", " ").title(),
                    "props": {"label": k.replace("_", " ").title(), "value": str(v)},
                }
                for i, (k, v) in enumerate(data.items())
            ]
        return [_text_block(f"```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```", prefix)]

    if isinstance(data, list) and data and isinstance(data[0], dict):
        columns = list(data[0].keys())
        rows = [[str(row.get(col, "")) for col in columns] for row in data]
        return [{
            "id": f"{prefix}_table",
            "type": "table",
            "title": None,
            "props": {
                "columns": [{"key": c, "label": c.replace("_", " ").title()} for c in columns],
                "rows": rows,
            },
        }]

    return [_text_block(json.dumps(data, indent=2, ensure_ascii=False), prefix)]


def _spec(
    blocks: list[dict[str, Any]],
    title: str,
    run_id: str | None,
    model: str,
) -> dict[str, Any]:
    effective = blocks or [_text_block("No output captured.", "ant_empty")]
    result: dict[str, Any] = {
        "version": "tilo/aip/v1",
        "title": title,
        "status": "ready",
        "blocks": effective,
        "views": [{"id": "result", "label": "Result", "block_ids": [b["id"] for b in effective]}],
        "actions": [],
        "provenance": [{"type": "anthropic_message", "id": model}],
        "memory_refs": [],
        "follow_ups": [],
    }
    if run_id:
        result["run_id"] = run_id
    return result


# --------------------------------------------------------------------------- #
# Public: direct conversion                                                    #
# --------------------------------------------------------------------------- #

def tilo_spec_from_message(
    response: Any,
    *,
    title: str = "Claude Result",
    run_id: str | None = None,
) -> dict[str, Any]:
    """Convert an Anthropic Messages API response into a Tilo AIP v1 spec.

    Args:
        response:  The object returned by ``client.messages.create()``.
        title:     Spec title shown in the artifact header.
        run_id:    Optional Tilo run_id for provenance.

    Returns:
        A Tilo AIP v1 spec dict, ready for ``ArtifactSpecV1.model_validate()``.
    """
    model = getattr(response, "model", "claude")
    blocks: list[dict[str, Any]] = []

    content = getattr(response, "content", []) or []
    for block in content:
        btype = getattr(block, "type", None)

        if btype == "text":
            text = getattr(block, "text", "") or ""
            if text.strip():
                try:
                    parsed = json.loads(text)
                    blocks.extend(_structured_blocks(parsed))
                except (json.JSONDecodeError, ValueError):
                    blocks.append(_text_block(text))

        elif btype == "tool_use":
            name = getattr(block, "name", "tool")
            inp = getattr(block, "input", {})
            blocks.append(_tool_use_block(name, inp))

        # Ignore other block types (e.g. thinking) gracefully

    return _spec(blocks, title, run_id, model)


# --------------------------------------------------------------------------- #
# Public: streaming handler                                                    #
# --------------------------------------------------------------------------- #

class TiloMessageHandler:
    """Accumulates Anthropic streaming text into Tilo AIP blocks.

    Compatible with both ``client.messages.stream()`` (managed) and
    ``client.messages.create(stream=True)`` (raw SSE).

    Example (managed stream):
        handler = TiloMessageHandler(title="Analysis")
        with client.messages.stream(model="claude-opus-4-8", ...) as stream:
            for text in stream.text_stream:
                handler.on_text(text)
        spec = handler.to_spec()

    Example (raw SSE):
        handler = TiloMessageHandler()
        with client.messages.create(..., stream=True) as stream:
            for event in stream:
                handler.on_event(event)
        spec = handler.to_spec()
    """

    def __init__(
        self,
        title: str = "Claude Result",
        run_id: str | None = None,
        model: str = "claude",
    ) -> None:
        self.title = title
        self.run_id = run_id
        self._model = model
        self._text_parts: list[str] = []
        self._tool_blocks: list[dict[str, Any]] = []

    # ------------------------------------------------------------------ #
    # Streaming callbacks                                                  #
    # ------------------------------------------------------------------ #

    def on_text(self, text: str) -> None:
        """Call with each text delta from ``stream.text_stream``."""
        if text:
            self._text_parts.append(text)

    def on_event(self, event: Any) -> None:
        """Call with raw SSE events from ``client.messages.create(stream=True)``."""
        try:
            etype = getattr(event, "type", None)
            if etype == "content_block_delta":
                delta = getattr(event, "delta", None)
                if delta and getattr(delta, "type", None) == "text_delta":
                    self._text_parts.append(getattr(delta, "text", "") or "")
            elif etype == "message_start":
                msg = getattr(event, "message", None)
                if msg:
                    model = getattr(msg, "model", None)
                    if model:
                        self._model = model
            elif etype == "content_block_stop":
                pass  # handled via on_text / accumulated
        except (AttributeError, TypeError):
            pass

    def on_tool_use(self, name: str, input_data: dict[str, Any] | str) -> None:
        """Manually record a tool use block (e.g. from ``stream.get_final_message()``)."""
        self._tool_blocks.append(_tool_use_block(name, input_data))

    # ------------------------------------------------------------------ #
    # Output                                                               #
    # ------------------------------------------------------------------ #

    def to_spec(self) -> dict[str, Any]:
        """Assemble accumulated stream into a Tilo AIP v1 spec."""
        blocks: list[dict[str, Any]] = []

        full_text = "".join(self._text_parts).strip()
        if full_text:
            try:
                parsed = json.loads(full_text)
                blocks.extend(_structured_blocks(parsed))
            except (json.JSONDecodeError, ValueError):
                blocks.append(_text_block(full_text))

        blocks.extend(self._tool_blocks)
        return _spec(blocks, self.title, self.run_id, self._model)

    def reset(self) -> None:
        """Clear accumulated state for reuse."""
        self._text_parts.clear()
        self._tool_blocks.clear()


# --------------------------------------------------------------------------- #
# Full AIP generation (recommended entry point)                                #
# --------------------------------------------------------------------------- #

def generate_aip_spec(
    client: Any,
    goal: str,
    *,
    model: str = "claude-opus-4-8",
    skill: str | None = "auto",
    document: str | None = None,
    memories: list[str] | None = None,
    language: str | None = None,
    max_tokens: int = 4096,
) -> Any:
    """Generate a full Tilo AIP spec by prompting Claude with the AIP format.

    Unlike ``tilo_spec_from_message()`` which converts existing output,
    this function prompts Claude to generate a rich, structured AIP spec
    directly — including chart, diff, timeline, confirmation, and
    memory_card blocks, organised into views with follow-up suggestions.

    Args:
        client:     An ``anthropic.Anthropic()`` instance.
        goal:       What the artifact should address.
        model:      Claude model (default: "claude-opus-4-8").
        skill:      "auto" to detect from goal, or one of:
                    "contract_review", "code_review", "sales_dashboard",
                    "trip_planning", "competitive_analysis", "data_analysis".
        document:   Optional document text (contract, PR diff, etc.).
        memories:   Optional list of recalled user preference strings.
        language:   "en" to force English, "zh" for Chinese output.
        max_tokens: Max tokens for the response (default: 4096).

    Returns:
        A validated ``ArtifactSpecV1`` instance.

    Example:
        import anthropic
        from tilo.adapters.anthropic_sdk import generate_aip_spec

        spec = generate_aip_spec(
            client=anthropic.Anthropic(),
            goal="Review this PR for security vulnerabilities.",
            skill="code_review",
            document=pr_diff,
        )
        print([b.type for b in spec.blocks])
        # → ["card", "diff", "table", "checklist", "confirmation", "memory_card"]
    """
    from tilo.generate import generate_with_anthropic
    return generate_with_anthropic(
        client, goal,
        model=model, skill=skill, document=document,
        memories=memories, language=language,
        max_tokens=max_tokens,
    )
