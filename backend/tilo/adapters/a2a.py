"""A2A (Agent-to-Agent) → Tilo AIP adapter (stub).

Converts Google A2A protocol task results into Tilo AIP specs.

Status: Interface only. Implementation planned for future milestone.
"""

from typing import Any


def a2a_task_to_spec(task_result: dict[str, Any]) -> dict[str, Any]:
    """Convert an A2A task result to a Tilo AIP spec. Stub."""
    return {
        "version": "tilo/aip/v1",
        "title": task_result.get("name", "A2A Task Result"),
        "status": "ready",
        "blocks": [
            {
                "id": "a2a_result",
                "type": "markdown",
                "props": {"content": str(task_result.get("output", "No output."))},
            },
        ],
        "views": [],
        "actions": [],
        "provenance": [],
        "memory_refs": [],
        "follow_ups": [],
    }
