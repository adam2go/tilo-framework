"""OpenAI → Tilo AIP adapter.

Converts OpenAI ChatCompletion (and streaming) responses into Tilo AIP specs.
No hard dependency on the openai package at import time — duck-typed interface.

Usage (direct conversion):
    from openai import OpenAI
    from tilo.adapters.openai import tilo_spec_from_completion

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Summarise the Q3 results"}],
    )
    spec = tilo_spec_from_completion(response)          # → Tilo AIP v1 dict
    # validated = ArtifactSpecV1.model_validate(spec)   # optional Pydantic step

Usage (streaming handler):
    from tilo.adapters.openai import TiloCompletionHandler

    handler = TiloCompletionHandler()
    for chunk in client.chat.completions.create(..., stream=True):
        handler.on_chunk(chunk)
    spec = handler.to_spec()

Usage (tool-call capture):
    # Tool calls are automatically captured as tool_preview blocks.
    response = client.chat.completions.create(
        model="gpt-4o",
        tools=[...],
        messages=[...],
    )
    spec = tilo_spec_from_completion(response)
    # tool_preview blocks appear for each tool call in the response
"""

from __future__ import annotations

import json
import uuid
from typing import Any


# --------------------------------------------------------------------------- #
# Internal helpers                                                             #
# --------------------------------------------------------------------------- #

def _new_id(prefix: str = "oai") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _text_block(text: str, block_id: str | None = None) -> dict[str, Any]:
    return {
        "id": block_id or _new_id("oai_text"),
        "type": "markdown",
        "title": None,
        "props": {"content": text.strip()},
    }


def _tool_call_block(
    name: str,
    arguments: str,
    block_id: str | None = None,
) -> dict[str, Any]:
    """Represent an OpenAI tool call as a tool_preview block."""
    try:
        parsed = json.loads(arguments)
        args_display = json.dumps(parsed, indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        args_display = arguments or ""
    return {
        "id": block_id or _new_id("oai_tool"),
        "type": "tool_preview",
        "title": name,
        "props": {
            "tool_name": name,
            "status": "pending",
            "output": args_display,
        },
    }


def _structured_block(data: Any, block_id: str | None = None) -> list[dict[str, Any]]:
    """Convert parsed JSON output into typed blocks (metric / table / markdown)."""
    bid = block_id or _new_id("oai_struct")
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
                    "id": f"{bid}_{i}",
                    "type": "metric",
                    "title": k.replace("_", " ").title(),
                    "props": {"label": k.replace("_", " ").title(), "value": str(v)},
                }
                for i, (k, v) in enumerate(data.items())
            ]
        return [_text_block(
            f"```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```", bid
        )]

    if isinstance(data, list) and data and isinstance(data[0], dict):
        columns = list(data[0].keys())
        rows = [[str(row.get(col, "")) for col in columns] for row in data]
        return [{
            "id": f"{bid}_table",
            "type": "table",
            "title": None,
            "props": {
                "columns": [{"key": c, "label": c.replace("_", " ").title()} for c in columns],
                "rows": rows,
            },
        }]

    return [_text_block(json.dumps(data, indent=2, ensure_ascii=False), bid)]


def _spec(
    blocks: list[dict[str, Any]],
    title: str,
    run_id: str | None,
    model: str,
) -> dict[str, Any]:
    effective = blocks or [_text_block("No output captured.", "oai_empty")]
    result: dict[str, Any] = {
        "version": "tilo/aip/v1",
        "title": title,
        "status": "ready",
        "blocks": effective,
        "views": [{"id": "result", "label": "Result", "block_ids": [b["id"] for b in effective]}],
        "actions": [],
        "provenance": [{"type": "openai_completion", "id": model}],
        "memory_refs": [],
        "follow_ups": [],
    }
    if run_id:
        result["run_id"] = run_id
    return result


def _blocks_from_message(message: Any) -> list[dict[str, Any]]:
    """Extract AIP blocks from a single OpenAI ChatCompletionMessage."""
    blocks: list[dict[str, Any]] = []

    # Text content
    content = getattr(message, "content", None)
    if content and isinstance(content, str) and content.strip():
        # Try parsing as structured JSON first
        try:
            parsed = json.loads(content)
            blocks.extend(_structured_block(parsed))
        except (json.JSONDecodeError, ValueError):
            blocks.append(_text_block(content))

    # Tool calls
    tool_calls = getattr(message, "tool_calls", None) or []
    for tc in tool_calls:
        fn = getattr(tc, "function", None)
        if fn:
            blocks.append(_tool_call_block(
                name=getattr(fn, "name", "tool"),
                arguments=getattr(fn, "arguments", ""),
            ))

    return blocks


# --------------------------------------------------------------------------- #
# Public: direct conversion                                                    #
# --------------------------------------------------------------------------- #

def tilo_spec_from_completion(
    response: Any,
    *,
    title: str = "OpenAI Result",
    run_id: str | None = None,
) -> dict[str, Any]:
    """Convert an OpenAI ChatCompletion response directly into a Tilo AIP v1 spec.

    Args:
        response:  The object returned by ``client.chat.completions.create()``.
        title:     Spec title (shown in the artifact header).
        run_id:    Optional Tilo run_id to embed in the spec for provenance.

    Returns:
        A Tilo AIP v1 spec dict, ready for ``ArtifactSpecV1.model_validate()``.
    """
    model = getattr(response, "model", "openai")
    blocks: list[dict[str, Any]] = []

    choices = getattr(response, "choices", []) or []
    for choice in choices:
        message = getattr(choice, "message", None)
        if message is not None:
            blocks.extend(_blocks_from_message(message))

    return _spec(blocks, title, run_id, model)


# --------------------------------------------------------------------------- #
# Public: streaming handler                                                    #
# --------------------------------------------------------------------------- #

class TiloCompletionHandler:
    """Accumulates OpenAI streaming chunks into Tilo AIP blocks.

    Compatible with OpenAI SDK v1+ streaming (``stream=True``).

    Example:
        handler = TiloCompletionHandler(title="Sales Briefing")
        for chunk in client.chat.completions.create(..., stream=True):
            handler.on_chunk(chunk)
        spec = handler.to_spec()
    """

    def __init__(
        self,
        title: str = "OpenAI Result",
        run_id: str | None = None,
    ) -> None:
        self.title = title
        self.run_id = run_id
        self._text_parts: list[str] = []
        self._tool_calls: dict[int, dict[str, str]] = {}  # index → {name, args}
        self._model: str = "openai"

    def on_chunk(self, chunk: Any) -> None:
        """Process one streaming chunk from ``client.chat.completions.create(stream=True)``."""
        try:
            model = getattr(chunk, "model", None)
            if model:
                self._model = model

            choices = getattr(chunk, "choices", []) or []
            for choice in choices:
                delta = getattr(choice, "delta", None)
                if delta is None:
                    continue

                # Accumulate text
                content = getattr(delta, "content", None)
                if content:
                    self._text_parts.append(content)

                # Accumulate tool call fragments
                tool_calls = getattr(delta, "tool_calls", None) or []
                for tc in tool_calls:
                    idx = getattr(tc, "index", 0)
                    fn = getattr(tc, "function", None)
                    if fn:
                        if idx not in self._tool_calls:
                            self._tool_calls[idx] = {"name": "", "args": ""}
                        name = getattr(fn, "name", "") or ""
                        args = getattr(fn, "arguments", "") or ""
                        self._tool_calls[idx]["name"] += name
                        self._tool_calls[idx]["args"] += args
        except (AttributeError, TypeError):
            pass

    def to_spec(self) -> dict[str, Any]:
        """Assemble accumulated chunks into a Tilo AIP v1 spec."""
        blocks: list[dict[str, Any]] = []

        full_text = "".join(self._text_parts).strip()
        if full_text:
            try:
                parsed = json.loads(full_text)
                blocks.extend(_structured_block(parsed))
            except (json.JSONDecodeError, ValueError):
                blocks.append(_text_block(full_text))

        for tc in self._tool_calls.values():
            if tc["name"]:
                blocks.append(_tool_call_block(tc["name"], tc["args"]))

        return _spec(blocks, self.title, self.run_id, self._model)

    def reset(self) -> None:
        """Clear accumulated state for reuse across multiple requests."""
        self._text_parts.clear()
        self._tool_calls.clear()
        self._model = "openai"
