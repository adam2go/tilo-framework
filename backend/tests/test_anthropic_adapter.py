"""Tests for the Anthropic → Tilo AIP adapter."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tilo.adapters.anthropic_sdk import TiloMessageHandler, tilo_spec_from_message


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

def _text_block_mock(text: str) -> MagicMock:
    b = MagicMock()
    b.type = "text"
    b.text = text
    return b


def _tool_use_block_mock(name: str, input_data: dict) -> MagicMock:
    b = MagicMock()
    b.type = "tool_use"
    b.name = name
    b.input = input_data
    return b


def _make_response(
    content_blocks: list,
    model: str = "claude-opus-4-8",
) -> MagicMock:
    resp = MagicMock()
    resp.model = model
    resp.content = content_blocks
    return resp


# --------------------------------------------------------------------------- #
# tilo_spec_from_message                                                       #
# --------------------------------------------------------------------------- #

class TestTiloSpecFromMessage:
    def test_text_block_becomes_markdown(self):
        spec = tilo_spec_from_message(_make_response([_text_block_mock("Hello from Claude.")]))
        assert spec["version"] == "tilo/aip/v1"
        types = [b["type"] for b in spec["blocks"]]
        assert "markdown" in types
        assert any("Hello from Claude." in b["props"].get("content", "") for b in spec["blocks"])

    def test_json_text_becomes_metric_blocks(self):
        spec = tilo_spec_from_message(
            _make_response([_text_block_mock('{"revenue": 500, "customers": 12}')])
        )
        assert any(b["type"] == "metric" for b in spec["blocks"])

    def test_json_array_becomes_table(self):
        spec = tilo_spec_from_message(
            _make_response([_text_block_mock('[{"name": "A", "val": "1"}, {"name": "B", "val": "2"}]')])
        )
        assert any(b["type"] == "table" for b in spec["blocks"])

    def test_tool_use_block_becomes_tool_preview(self):
        spec = tilo_spec_from_message(
            _make_response([_tool_use_block_mock("web_search", {"query": "tilo framework"})])
        )
        tool_blocks = [b for b in spec["blocks"] if b["type"] == "tool_preview"]
        assert len(tool_blocks) == 1
        assert tool_blocks[0]["props"]["tool_name"] == "web_search"
        assert "tilo framework" in tool_blocks[0]["props"]["output"]

    def test_mixed_text_and_tool_use(self):
        spec = tilo_spec_from_message(_make_response([
            _text_block_mock("I found the following:"),
            _tool_use_block_mock("lookup", {"id": "42"}),
        ]))
        types = [b["type"] for b in spec["blocks"]]
        assert "markdown" in types
        assert "tool_preview" in types

    def test_empty_response_gives_placeholder(self):
        spec = tilo_spec_from_message(_make_response([]))
        assert len(spec["blocks"]) == 1
        assert "No output" in spec["blocks"][0]["props"]["content"]

    def test_whitespace_only_text_ignored(self):
        spec = tilo_spec_from_message(_make_response([_text_block_mock("   \n  ")]))
        assert "No output" in spec["blocks"][0]["props"]["content"]

    def test_custom_title_and_run_id(self):
        spec = tilo_spec_from_message(
            _make_response([_text_block_mock("x")]),
            title="Board Summary",
            run_id="run-55",
        )
        assert spec["title"] == "Board Summary"
        assert spec["run_id"] == "run-55"

    def test_provenance_contains_model(self):
        spec = tilo_spec_from_message(
            _make_response([_text_block_mock("hi")], model="claude-haiku-4-5-20251001")
        )
        assert spec["provenance"][0]["type"] == "anthropic_message"
        assert spec["provenance"][0]["id"] == "claude-haiku-4-5-20251001"

    def test_view_covers_all_blocks(self):
        spec = tilo_spec_from_message(_make_response([_text_block_mock("hi")]))
        assert set(spec["views"][0]["block_ids"]) == {b["id"] for b in spec["blocks"]}

    def test_invalid_json_text_falls_back_to_markdown(self):
        spec = tilo_spec_from_message(_make_response([_text_block_mock("{bad json")]))
        assert spec["blocks"][0]["type"] == "markdown"

    def test_unknown_block_types_ignored(self):
        unknown = MagicMock()
        unknown.type = "thinking"  # Anthropic extended thinking block
        spec = tilo_spec_from_message(
            _make_response([unknown, _text_block_mock("real answer")])
        )
        assert any("real answer" in b["props"].get("content", "") for b in spec["blocks"])


# --------------------------------------------------------------------------- #
# TiloMessageHandler (streaming)                                               #
# --------------------------------------------------------------------------- #

class TestTiloMessageHandler:
    def test_on_text_accumulates(self):
        handler = TiloMessageHandler()
        handler.on_text("Hello")
        handler.on_text(", Claude!")
        spec = handler.to_spec()
        assert "Hello, Claude!" in spec["blocks"][0]["props"]["content"]

    def test_json_text_becomes_metric(self):
        handler = TiloMessageHandler()
        handler.on_text('{"score": 95, "grade": "A"}')
        spec = handler.to_spec()
        assert any(b["type"] == "metric" for b in spec["blocks"])

    def test_on_tool_use_adds_tool_preview(self):
        handler = TiloMessageHandler()
        handler.on_text("Here is the analysis.")
        handler.on_tool_use("calculator", {"expression": "2 + 2"})
        spec = handler.to_spec()
        types = [b["type"] for b in spec["blocks"]]
        assert "markdown" in types
        assert "tool_preview" in types

    def test_on_event_text_delta(self):
        handler = TiloMessageHandler()
        event = MagicMock()
        event.type = "content_block_delta"
        event.delta.type = "text_delta"
        event.delta.text = "streamed text"
        handler.on_event(event)
        spec = handler.to_spec()
        assert "streamed text" in spec["blocks"][0]["props"]["content"]

    def test_on_event_message_start_captures_model(self):
        handler = TiloMessageHandler()
        event = MagicMock()
        event.type = "message_start"
        event.message.model = "claude-opus-4-8"
        handler.on_event(event)
        handler.on_text("hi")
        spec = handler.to_spec()
        assert spec["provenance"][0]["id"] == "claude-opus-4-8"

    def test_on_event_unknown_type_ignored(self):
        handler = TiloMessageHandler()
        event = MagicMock()
        event.type = "ping"
        handler.on_event(event)  # should not raise
        handler.on_text("still works")
        assert handler.to_spec() is not None

    def test_empty_handler_gives_placeholder(self):
        handler = TiloMessageHandler()
        spec = handler.to_spec()
        assert "No output" in spec["blocks"][0]["props"]["content"]

    def test_reset_clears_state(self):
        handler = TiloMessageHandler()
        handler.on_text("first run")
        handler.reset()
        handler.on_text("second run")
        spec = handler.to_spec()
        content = spec["blocks"][0]["props"]["content"]
        assert "second run" in content
        assert "first run" not in content

    def test_malformed_event_ignored(self):
        handler = TiloMessageHandler()
        handler.on_event(None)
        handler.on_event("not an event")
        assert handler.to_spec() is not None
