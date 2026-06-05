"""ACP (Agent Communication Protocol) → Tilo AIP adapter.

Converts ACP messages into Tilo AIP specs.

ACP messages carry a list of `parts` (MessagePart), each with a
`content_type` and `content`:
    text/plain            → markdown
    text/markdown         → markdown
    application/json      → metric / table / markdown (by shape)
    image/*               → card (with content_url)
    other                 → card

Usage:
    from tilo.adapters.acp import acp_message_to_spec

    spec = acp_message_to_spec(message)          # → Tilo AIP v1 dict

Reference: https://github.com/i-am-bee/acp
"""

from __future__ import annotations

import json
from typing import Any


def _json_to_blocks(data: Any, block_id: str) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        is_metrics = (
            len(data) <= 8
            and all(
                isinstance(v, (int, float)) or (isinstance(v, str) and len(v) < 40)
                for v in data.values()
            )
        )
        if is_metrics:
            return [
                {
                    "id": f"{block_id}_{i}",
                    "type": "metric",
                    "title": k.replace("_", " ").title(),
                    "props": {"label": k.replace("_", " ").title(), "value": str(v)},
                }
                for i, (k, v) in enumerate(data.items())
            ]
        return [{
            "id": block_id,
            "type": "markdown",
            "props": {"content": f"```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```"},
        }]

    if isinstance(data, list) and data and isinstance(data[0], dict):
        columns = list(data[0].keys())
        rows = [[str(row.get(col, "")) for col in columns] for row in data]
        return [{
            "id": f"{block_id}_table",
            "type": "table",
            "props": {
                "columns": [{"key": c, "label": c.replace("_", " ").title()} for c in columns],
                "rows": rows,
            },
        }]

    return [{
        "id": block_id,
        "type": "markdown",
        "props": {"content": json.dumps(data, indent=2, ensure_ascii=False)},
    }]


def _part_to_blocks(part: dict[str, Any], block_id: str) -> list[dict[str, Any]]:
    """Map a single ACP MessagePart to one or more Tilo blocks."""
    content_type = (part.get("content_type") or part.get("contentType") or "text/plain").lower()
    content = part.get("content")
    content_url = part.get("content_url") or part.get("contentUrl")
    name = part.get("name")

    if content_type.startswith("image/"):
        return [{
            "id": block_id,
            "type": "card",
            "title": name or "Image",
            "props": {
                "title": name or "Image",
                "content": content_url or content_type,
                "uri": content_url,
                "mime_type": content_type,
            },
        }]

    if content_type == "application/json":
        data: Any = content
        if isinstance(content, str):
            try:
                data = json.loads(content)
            except (json.JSONDecodeError, TypeError):
                data = content
        return _json_to_blocks(data, block_id)

    if content_type in ("text/plain", "text/markdown", "text/x-markdown"):
        text = str(content or "")
        if not text.strip():
            return []
        return [{"id": block_id, "type": "markdown", "props": {"content": text}}]

    # Unknown content type → card with a reference.
    return [{
        "id": block_id,
        "type": "card",
        "title": name or content_type,
        "props": {
            "title": name or content_type,
            "content": (content_url or str(content) or content_type)[:500],
            "uri": content_url,
            "mime_type": content_type,
        },
    }]


def acp_message_to_spec(
    message: dict[str, Any],
    *,
    title: str | None = None,
) -> dict[str, Any]:
    """Convert an ACP message into a Tilo AIP v1 spec.

    Args:
        message: An ACP Message dict (with `parts`, or a legacy `body`).
        title:   Optional spec title.

    Returns:
        A Tilo AIP v1 spec dict.
    """
    blocks: list[dict[str, Any]] = []

    parts = message.get("parts") or []
    for pi, part in enumerate(parts):
        blocks.extend(_part_to_blocks(part, f"acp_{pi}"))

    # Legacy / simple shape: a plain `body` string.
    if not blocks and message.get("body") is not None:
        blocks.append({
            "id": "acp_body",
            "type": "markdown",
            "props": {"content": str(message["body"])},
        })
    if not blocks:
        blocks.append({
            "id": "acp_empty",
            "type": "markdown",
            "props": {"content": "No content."},
        })

    spec_title = (
        title
        or message.get("subject")
        or (f"ACP Message ({message['role']})" if message.get("role") else None)
        or "ACP Message"
    )

    return {
        "version": "tilo/aip/v1",
        "title": spec_title,
        "status": "ready",
        "blocks": blocks,
        "views": [{"id": "result", "label": "Message", "block_ids": [b["id"] for b in blocks]}],
        "actions": [],
        "provenance": [{"type": "acp_message", "id": str(message.get("id", "acp"))}],
        "memory_refs": [],
        "follow_ups": [],
    }
