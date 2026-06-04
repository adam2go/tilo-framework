"""Tests for the OpenAI → Tilo AIP adapter."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tilo.adapters.openai import TiloCompletionHandler, tilo_spec_from_completion


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

def _make_response(
    content: str | None = None,
    tool_calls: list[tuple[str, str]] | None = None,
    model: str = "gpt-4o",
) -> MagicMock:
    """Build a minimal OpenAI ChatCompletion mock."""
    message = MagicMock()
    message.content = content
    if tool_calls:
        tc_list = []
        for name, args in tool_calls:
            tc = MagicMock()
            tc.function.name = name
            tc.function.arguments = args
            tc_list.append(tc)
        message.tool_calls = tc_list
    else:
        message.tool_calls = []

    choice = MagicMock()
    choice.message = message

    response = MagicMock()
    response.model = model
    response.choices = [choice]
    return response


def _make_chunk(content: str | None = None, tool_index: int | None = None,
                tool_name: str | None = None, tool_args: str | None = None,
                model: str | None = None) -> MagicMock:
    delta = MagicMock()
    delta.content = content
    if tool_index is not None:
        tc = MagicMock()
        tc.index = tool_index
        tc.function.name = tool_name or ""
        tc.function.arguments = tool_args or ""
        delta.tool_calls = [tc]
    else:
        delta.tool_calls = []

    choice = MagicMock()
    choice.delta = delta

    chunk = MagicMock()
    chunk.model = model
    chunk.choices = [choice]
    return chunk


# --------------------------------------------------------------------------- #
# tilo_spec_from_completion                                                    #
# --------------------------------------------------------------------------- #

class TestTiloSpecFromCompletion:
    def test_text_content_becomes_markdown(self):
        spec = tilo_spec_from_completion(_make_response("Hello, world!"))
        assert spec["version"] == "tilo/aip/v1"
        assert spec["status"] == "ready"
        types = [b["type"] for b in spec["blocks"]]
        assert "markdown" in types
        assert any("Hello, world!" in b["props"].get("content", "") for b in spec["blocks"])

    def test_json_content_becomes_metric_blocks(self):
        spec = tilo_spec_from_completion(_make_response('{"revenue": 1000, "deals": 5}'))
        types = [b["type"] for b in spec["blocks"]]
        assert "metric" in types

    def test_json_array_of_dicts_becomes_table(self):
        spec = tilo_spec_from_completion(
            _make_response('[{"name": "Alice", "score": "90"}, {"name": "Bob", "score": "80"}]')
        )
        types = [b["type"] for b in spec["blocks"]]
        assert "table" in types

    def test_tool_calls_become_tool_preview(self):
        spec = tilo_spec_from_completion(
            _make_response(tool_calls=[("web_search", '{"query": "tilo framework"}')])
        )
        tool_blocks = [b for b in spec["blocks"] if b["type"] == "tool_preview"]
        assert len(tool_blocks) == 1
        assert tool_blocks[0]["props"]["tool_name"] == "web_search"
        assert tool_blocks[0]["props"]["status"] == "pending"

    def test_multiple_tool_calls(self):
        spec = tilo_spec_from_completion(
            _make_response(tool_calls=[
                ("search", '{"q": "ai"}'),
                ("calculator", '{"expr": "1+1"}'),
            ])
        )
        tool_blocks = [b for b in spec["blocks"] if b["type"] == "tool_preview"]
        assert len(tool_blocks) == 2
        names = {b["props"]["tool_name"] for b in tool_blocks}
        assert names == {"search", "calculator"}

    def test_null_content_with_tools_only(self):
        spec = tilo_spec_from_completion(
            _make_response(content=None, tool_calls=[("lookup", "{}")])
        )
        assert any(b["type"] == "tool_preview" for b in spec["blocks"])

    def test_empty_response_gives_placeholder(self):
        spec = tilo_spec_from_completion(_make_response(content=None))
        assert len(spec["blocks"]) == 1
        assert "No output" in spec["blocks"][0]["props"]["content"]

    def test_custom_title(self):
        spec = tilo_spec_from_completion(_make_response("x"), title="My Report")
        assert spec["title"] == "My Report"

    def test_run_id_attached(self):
        spec = tilo_spec_from_completion(_make_response("x"), run_id="run-123")
        assert spec.get("run_id") == "run-123"

    def test_provenance_contains_model(self):
        spec = tilo_spec_from_completion(_make_response("x", model="gpt-4o-mini"))
        assert spec["provenance"][0]["type"] == "openai_completion"
        assert spec["provenance"][0]["id"] == "gpt-4o-mini"

    def test_view_covers_all_blocks(self):
        spec = tilo_spec_from_completion(_make_response("text"))
        view_ids = set(spec["views"][0]["block_ids"])
        block_ids = {b["id"] for b in spec["blocks"]}
        assert view_ids == block_ids

    def test_invalid_json_falls_back_to_markdown(self):
        spec = tilo_spec_from_completion(_make_response("not json {"))
        assert spec["blocks"][0]["type"] == "markdown"


# --------------------------------------------------------------------------- #
# TiloCompletionHandler (streaming)                                            #
# --------------------------------------------------------------------------- #

class TestTiloCompletionHandler:
    def test_text_chunks_accumulated(self):
        handler = TiloCompletionHandler()
        handler.on_chunk(_make_chunk(content="Hello"))
        handler.on_chunk(_make_chunk(content=", world!"))
        spec = handler.to_spec()
        content = spec["blocks"][0]["props"]["content"]
        assert "Hello" in content and "world" in content

    def test_json_chunks_become_metric_blocks(self):
        handler = TiloCompletionHandler()
        handler.on_chunk(_make_chunk(content='{"a": 1'))
        handler.on_chunk(_make_chunk(content=', "b": 2}'))
        spec = handler.to_spec()
        assert any(b["type"] == "metric" for b in spec["blocks"])

    def test_tool_call_chunks_accumulated(self):
        handler = TiloCompletionHandler()
        handler.on_chunk(_make_chunk(tool_index=0, tool_name="search", tool_args=""))
        handler.on_chunk(_make_chunk(tool_index=0, tool_name="", tool_args='{"q": "tilo"}'))
        spec = handler.to_spec()
        tool_blocks = [b for b in spec["blocks"] if b["type"] == "tool_preview"]
        assert len(tool_blocks) == 1
        assert tool_blocks[0]["props"]["tool_name"] == "search"

    def test_model_captured_from_chunk(self):
        handler = TiloCompletionHandler()
        handler.on_chunk(_make_chunk(content="hi", model="gpt-4o"))
        spec = handler.to_spec()
        assert spec["provenance"][0]["id"] == "gpt-4o"

    def test_empty_handler_gives_placeholder(self):
        handler = TiloCompletionHandler()
        spec = handler.to_spec()
        assert "No output" in spec["blocks"][0]["props"]["content"]

    def test_reset_clears_state(self):
        handler = TiloCompletionHandler()
        handler.on_chunk(_make_chunk(content="first"))
        handler.reset()
        handler.on_chunk(_make_chunk(content="second"))
        spec = handler.to_spec()
        assert "second" in spec["blocks"][0]["props"]["content"]
        assert "first" not in spec["blocks"][0]["props"]["content"]

    def test_malformed_chunk_ignored(self):
        handler = TiloCompletionHandler()
        handler.on_chunk(None)  # should not raise
        handler.on_chunk("not a chunk")
        assert handler.to_spec() is not None

    def test_custom_title_and_run_id(self):
        handler = TiloCompletionHandler(title="Pipeline", run_id="r-99")
        handler.on_chunk(_make_chunk(content="done"))
        spec = handler.to_spec()
        assert spec["title"] == "Pipeline"
        assert spec["run_id"] == "r-99"
