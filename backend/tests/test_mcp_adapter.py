"""Tests for the MCP → Tilo AIP adapter."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tilo.adapters.mcp import mcp_content_to_blocks, mcp_tool_result_to_spec


def test_mcp_text_content_to_markdown_block() -> None:
    content = [{"type": "text", "text": "Hello from MCP tool"}]
    blocks = mcp_content_to_blocks(content)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "markdown"
    assert blocks[0]["props"]["content"] == "Hello from MCP tool"


def test_mcp_image_content_to_image_block() -> None:
    content = [{"type": "image", "data": "base64data==", "mimeType": "image/png"}]
    blocks = mcp_content_to_blocks(content)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "image"
    assert blocks[0]["props"]["src"] == "base64data=="
    assert blocks[0]["props"]["mime_type"] == "image/png"


def test_mcp_resource_content_to_card_block() -> None:
    content = [{"type": "resource", "resource": {"uri": "file://test.md", "name": "Test File", "text": "Contents"}}]
    blocks = mcp_content_to_blocks(content)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "card"
    assert blocks[0]["props"]["uri"] == "file://test.md"


def test_mcp_mixed_content() -> None:
    content = [
        {"type": "text", "text": "Analysis result:"},
        {"type": "image", "data": "img==", "mimeType": "image/jpeg"},
        {"type": "text", "text": "Conclusion: all good."},
    ]
    blocks = mcp_content_to_blocks(content)
    assert len(blocks) == 3
    assert blocks[0]["type"] == "markdown"
    assert blocks[1]["type"] == "image"
    assert blocks[2]["type"] == "markdown"


def test_mcp_tool_result_to_spec() -> None:
    content = [{"type": "text", "text": "Search results found 5 items."}]
    spec = mcp_tool_result_to_spec("web_search", content)
    assert spec["version"] == "tilo/aip/v1"
    assert spec["title"] == "web_search Result"
    assert len(spec["blocks"]) == 1
    assert len(spec["views"]) == 1
    assert spec["views"][0]["label"] == "Result"


def test_mcp_error_result() -> None:
    content = [{"type": "text", "text": "Connection timeout"}]
    spec = mcp_tool_result_to_spec("api_call", content, is_error=True)
    assert spec["blocks"][0]["id"] == "mcp_error"
    assert spec["blocks"][0]["props"]["severity"] == "high"
    assert len(spec["blocks"]) == 2
