"""ACP (Agent Communication Protocol) → Tilo AIP adapter (stub).

Converts ACP messages into Tilo AIP specs.

Status: Interface only. Implementation planned for future milestone.
"""

from typing import Any


def acp_message_to_spec(message: dict[str, Any]) -> dict[str, Any]:
    """Convert an ACP message to a Tilo AIP spec. Stub."""
    return {
        "version": "tilo/aip/v1",
        "title": message.get("subject", "ACP Message"),
        "status": "ready",
        "blocks": [
            {
                "id": "acp_content",
                "type": "markdown",
                "props": {"content": str(message.get("body", "No content."))},
            },
        ],
        "views": [],
        "actions": [],
        "provenance": [],
        "memory_refs": [],
        "follow_ups": [],
    }
