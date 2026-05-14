"""MCP → Tilo AIP adapter.

Converts MCP (Model Context Protocol) tool results into Tilo ArtifactBlocks.

Usage:
    from tilo.adapters.mcp import mcp_content_to_blocks

    blocks = mcp_content_to_blocks(mcp_result.content)

Mapping:
    TextContent   → markdown block
    ImageContent  → image block
    EmbeddedResource → card block with metadata
"""

from typing import Any


def mcp_content_to_blocks(content: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert a list of MCP Content items to Tilo ArtifactBlocks.

    MCP Content follows the spec at https://modelcontextprotocol.io
    Each item has a "type" field: "text", "image", or "resource".

    Args:
        content: List of MCP Content dicts, each with at minimum a "type" field.

    Returns:
        List of Tilo ArtifactBlock dicts ready for inclusion in a spec.
    """
    blocks: list[dict[str, Any]] = []
    for i, item in enumerate(content):
        content_type = item.get("type", "text")
        block_id = f"mcp_{i}"

        if content_type == "text":
            blocks.append({
                "id": block_id,
                "type": "markdown",
                "title": None,
                "props": {
                    "content": item.get("text", ""),
                },
            })

        elif content_type == "image":
            blocks.append({
                "id": block_id,
                "type": "image",
                "title": None,
                "props": {
                    "src": item.get("data", ""),
                    "alt": item.get("mimeType", "image"),
                    "mime_type": item.get("mimeType", "image/png"),
                    "encoding": "base64",
                },
            })

        elif content_type == "resource":
            resource = item.get("resource", {})
            blocks.append({
                "id": block_id,
                "type": "card",
                "title": resource.get("name") or resource.get("uri", "Resource"),
                "props": {
                    "title": resource.get("name") or "Embedded Resource",
                    "content": resource.get("text", ""),
                    "uri": resource.get("uri"),
                    "mime_type": resource.get("mimeType"),
                },
            })

        else:
            # Unknown MCP content type → generic block
            blocks.append({
                "id": block_id,
                "type": "card",
                "title": f"MCP {content_type}",
                "props": item,
            })

    return blocks


def mcp_tool_result_to_spec(
    tool_name: str,
    content: list[dict[str, Any]],
    *,
    is_error: bool = False,
) -> dict[str, Any]:
    """Convert a complete MCP tool result into a minimal Tilo AIP spec.

    This creates a ready-to-render spec with a single "Result" view.
    """
    blocks = mcp_content_to_blocks(content)

    if is_error:
        blocks.insert(0, {
            "id": "mcp_error",
            "type": "card",
            "title": "Tool Error",
            "props": {
                "title": f"Error from {tool_name}",
                "content": "The tool returned an error. See details below.",
                "severity": "high",
            },
        })

    return {
        "version": "tilo/aip/v1",
        "title": f"{tool_name} Result",
        "status": "ready",
        "blocks": blocks,
        "views": [
            {
                "id": "result",
                "label": "Result",
                "block_ids": [b["id"] for b in blocks],
            },
        ],
        "actions": [],
        "provenance": [],
        "memory_refs": [],
        "follow_ups": [],
    }
