"""A2A (Agent2Agent) → Tilo AIP adapter.

Converts A2A protocol task results into Tilo AIP specs.

A2A tasks carry `artifacts`, each with typed `parts`:
    TextPart  {"type": "text", "text": "..."}            → markdown
    DataPart  {"type": "data", "data": {...}}             → metric / table / markdown
    FilePart  {"type": "file", "file": {...}}             → card (with uri / mime)

Usage:
    from tilo.adapters.a2a import a2a_task_to_spec

    spec = a2a_task_to_spec(task_result)         # → Tilo AIP v1 dict
    # ArtifactSpecV1.model_validate(spec)          # optional validation

Reference: https://github.com/google/A2A
"""

from __future__ import annotations

import json
from typing import Any


def _data_to_blocks(data: Any, block_id: str) -> list[dict[str, Any]]:
    """Map a DataPart payload to metric / table / markdown blocks."""
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
    """Map a single A2A Part to one or more Tilo blocks."""
    ptype = part.get("type") or part.get("kind") or "text"

    if ptype == "text":
        text = part.get("text", "")
        if not text.strip():
            return []
        return [{"id": block_id, "type": "markdown", "props": {"content": text}}]

    if ptype == "data":
        return _data_to_blocks(part.get("data", {}), block_id)

    if ptype == "file":
        file_info = part.get("file", {})
        name = file_info.get("name") or "File"
        return [{
            "id": block_id,
            "type": "card",
            "title": name,
            "props": {
                "title": name,
                "content": file_info.get("uri") or file_info.get("mimeType") or "Embedded file",
                "uri": file_info.get("uri"),
                "mime_type": file_info.get("mimeType"),
            },
        }]

    # Unknown part type → generic card
    return [{
        "id": block_id,
        "type": "card",
        "title": f"A2A {ptype}",
        "props": {"title": f"A2A {ptype}", "content": json.dumps(part, ensure_ascii=False)[:500]},
    }]


def a2a_task_to_spec(
    task_result: dict[str, Any],
    *,
    title: str | None = None,
) -> dict[str, Any]:
    """Convert an A2A task result into a Tilo AIP v1 spec.

    Args:
        task_result: An A2A Task dict (with `artifacts` and/or `status`).
        title:       Optional spec title (defaults to the task name / id).

    Returns:
        A Tilo AIP v1 spec dict.
    """
    blocks: list[dict[str, Any]] = []

    # Collect parts from all artifacts.
    artifacts = task_result.get("artifacts") or []
    for ai, artifact in enumerate(artifacts):
        for pi, part in enumerate(artifact.get("parts") or []):
            blocks.extend(_part_to_blocks(part, f"a2a_{ai}_{pi}"))

    # Fallback: a status message, or a plain `output`, or nothing.
    if not blocks:
        status = task_result.get("status") or {}
        message = status.get("message") if isinstance(status, dict) else None
        if isinstance(message, dict):
            for pi, part in enumerate(message.get("parts") or []):
                blocks.extend(_part_to_blocks(part, f"a2a_msg_{pi}"))
    if not blocks and task_result.get("output") is not None:
        blocks.append({
            "id": "a2a_output",
            "type": "markdown",
            "props": {"content": str(task_result["output"])},
        })
    if not blocks:
        blocks.append({
            "id": "a2a_empty",
            "type": "markdown",
            "props": {"content": "No output."},
        })

    state = ""
    status = task_result.get("status")
    if isinstance(status, dict):
        state = status.get("state", "")

    spec_title = (
        title
        or task_result.get("name")
        or (f"A2A Task ({state})" if state else None)
        or "A2A Task Result"
    )

    return {
        "version": "tilo/aip/v1",
        "title": spec_title,
        "status": "ready",
        "blocks": blocks,
        "views": [{"id": "result", "label": "Result", "block_ids": [b["id"] for b in blocks]}],
        "actions": [],
        "provenance": [{"type": "a2a_task", "id": str(task_result.get("id", "a2a"))}],
        "memory_refs": [],
        "follow_ups": [],
    }
