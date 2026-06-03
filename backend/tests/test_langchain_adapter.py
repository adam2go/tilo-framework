"""Tests for the LangChain → Tilo AIP adapter."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tilo.adapters.langchain import TiloCallbackHandler, langchain_result_to_spec


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

def _make_llm_response(text: str) -> MagicMock:
    """Build a minimal LangChain LLMResult mock."""
    gen = MagicMock()
    gen.text = text
    gen.message = MagicMock()
    gen.message.content = text
    response = MagicMock()
    response.generations = [[gen]]
    return response


def _make_agent_finish(output: str) -> MagicMock:
    finish = MagicMock()
    finish.return_values = {"output": output}
    return finish


# --------------------------------------------------------------------------- #
# langchain_result_to_spec                                                     #
# --------------------------------------------------------------------------- #

class TestLangchainResultToSpec:
    def test_string_output_becomes_markdown(self):
        spec = langchain_result_to_spec("Chain", {"output": "Hello, world."})
        assert spec["version"] == "tilo/aip/v1"
        assert spec["title"] == "Chain"
        assert spec["status"] == "ready"
        assert len(spec["blocks"]) == 1
        assert spec["blocks"][0]["type"] == "markdown"
        assert "Hello, world." in spec["blocks"][0]["props"]["content"]

    def test_view_references_all_block_ids(self):
        spec = langchain_result_to_spec("Chain", {"a": "one", "b": "two"})
        view_ids = spec["views"][0]["block_ids"]
        block_ids = [b["id"] for b in spec["blocks"]]
        assert set(view_ids) == set(block_ids)

    def test_dict_metrics_become_metric_blocks(self):
        spec = langchain_result_to_spec("Metrics", {"data": {"revenue": 1000, "deals": 5}})
        types = [b["type"] for b in spec["blocks"]]
        assert "metric" in types

    def test_large_dict_becomes_json_markdown(self):
        big = {f"key_{i}": f"value_{i}_long_enough_to_not_be_metric" for i in range(10)}
        spec = langchain_result_to_spec("Big", {"data": big})
        types = [b["type"] for b in spec["blocks"]]
        assert "markdown" in types
        assert "metric" not in types

    def test_list_of_dicts_becomes_table(self):
        rows = [{"name": "Alice", "score": "90"}, {"name": "Bob", "score": "80"}]
        spec = langchain_result_to_spec("Table", {"results": rows})
        types = [b["type"] for b in spec["blocks"]]
        assert "table" in types
        table = next(b for b in spec["blocks"] if b["type"] == "table")
        assert table["props"]["columns"][0]["key"] == "name"
        assert ["Alice", "90"] in table["props"]["rows"]

    def test_empty_outputs_gives_placeholder(self):
        spec = langchain_result_to_spec("Empty", {})
        assert len(spec["blocks"]) == 1
        assert "No output" in spec["blocks"][0]["props"]["content"]

    def test_run_id_attached_when_provided(self):
        spec = langchain_result_to_spec("Chain", {"out": "x"}, run_id="run-123")
        assert spec.get("run_id") == "run-123"

    def test_run_id_absent_when_not_provided(self):
        spec = langchain_result_to_spec("Chain", {"out": "x"})
        assert "run_id" not in spec

    def test_provenance_set(self):
        spec = langchain_result_to_spec("MyChain", {"out": "y"})
        assert spec["provenance"][0]["type"] == "langchain_chain"
        assert spec["provenance"][0]["id"] == "MyChain"


# --------------------------------------------------------------------------- #
# TiloCallbackHandler                                                          #
# --------------------------------------------------------------------------- #

class TestTiloCallbackHandlerLLM:
    def test_captures_llm_text_as_markdown(self):
        h = TiloCallbackHandler()
        h.on_llm_end(_make_llm_response("Agent output here."))
        spec = h.to_spec()
        assert any("Agent output here." in b["props"]["content"] for b in spec["blocks"])

    def test_empty_llm_text_not_added(self):
        h = TiloCallbackHandler()
        h.on_llm_end(_make_llm_response(""))
        assert len(h.blocks) == 0

    def test_whitespace_only_llm_text_not_added(self):
        h = TiloCallbackHandler()
        h.on_llm_end(_make_llm_response("   \n  "))
        assert len(h.blocks) == 0

    def test_malformed_response_ignored(self):
        h = TiloCallbackHandler()
        h.on_llm_end(None)  # should not raise
        assert len(h.blocks) == 0


class TestTiloCallbackHandlerTools:
    def test_tool_success_becomes_tool_preview(self):
        h = TiloCallbackHandler()
        h.on_tool_start({"name": "search"}, "query", run_id="t1")
        h.on_tool_end("Search results.", run_id="t1")
        spec = h.to_spec()
        tool_blocks = [b for b in spec["blocks"] if b["type"] == "tool_preview"]
        assert len(tool_blocks) == 1
        assert tool_blocks[0]["props"]["tool_name"] == "search"
        assert tool_blocks[0]["props"]["status"] == "success"
        assert "Search results." in tool_blocks[0]["props"]["output"]

    def test_tool_error_has_error_status(self):
        h = TiloCallbackHandler()
        h.on_tool_start({"name": "calc"}, "1/0", run_id="t2")
        h.on_tool_error(ZeroDivisionError("division by zero"), run_id="t2")
        spec = h.to_spec()
        error_blocks = [
            b for b in spec["blocks"]
            if b["type"] == "tool_preview" and b["props"]["status"] == "error"
        ]
        assert len(error_blocks) == 1
        assert error_blocks[0]["props"]["tool_name"] == "calc"

    def test_tool_without_start_uses_generic_name(self):
        h = TiloCallbackHandler()
        h.on_tool_end("output", run_id="unknown")
        spec = h.to_spec()
        tool_blocks = [b for b in spec["blocks"] if b["type"] == "tool_preview"]
        assert tool_blocks[0]["props"]["tool_name"] == "tool"

    def test_multiple_tool_calls_tracked_by_run_id(self):
        h = TiloCallbackHandler()
        h.on_tool_start({"name": "search"}, "q", run_id="r1")
        h.on_tool_start({"name": "calculator"}, "1+1", run_id="r2")
        h.on_tool_end("results", run_id="r1")
        h.on_tool_end("2", run_id="r2")
        names = [b["props"]["tool_name"] for b in h.blocks if b["type"] == "tool_preview"]
        assert "search" in names
        assert "calculator" in names


class TestTiloCallbackHandlerAgent:
    def test_agent_finish_adds_unique_output(self):
        h = TiloCallbackHandler()
        h.on_agent_finish(_make_agent_finish("The final answer."))
        spec = h.to_spec()
        assert any("The final answer." in b["props"]["content"] for b in spec["blocks"])

    def test_agent_finish_deduplicates_llm_output(self):
        h = TiloCallbackHandler()
        h.on_llm_end(_make_llm_response("Same answer."))
        h.on_agent_finish(_make_agent_finish("Same answer."))
        md_blocks = [b for b in h.blocks if b["type"] == "markdown"]
        assert len(md_blocks) == 1

    def test_agent_finish_empty_output_ignored(self):
        h = TiloCallbackHandler()
        h.on_agent_finish(_make_agent_finish(""))
        assert len(h.blocks) == 0


class TestTiloCallbackHandlerChain:
    def test_chain_end_captures_when_no_blocks(self):
        h = TiloCallbackHandler()
        h.on_chain_end({"output": "Chain fallback."})
        assert any("Chain fallback." in b["props"]["content"] for b in h.blocks)

    def test_chain_end_skipped_when_blocks_exist(self):
        h = TiloCallbackHandler()
        h.on_llm_end(_make_llm_response("LLM output."))
        h.on_chain_end({"output": "Should not appear."})
        contents = [b["props"].get("content", "") for b in h.blocks]
        assert not any("Should not appear." in c for c in contents)

    def test_chain_end_dict_output_becomes_blocks(self):
        h = TiloCallbackHandler()
        h.on_chain_end({"metrics": {"a": 1, "b": 2}})
        assert any(b["type"] == "metric" for b in h.blocks)

    def test_chain_end_non_dict_outputs_ignored(self):
        h = TiloCallbackHandler()
        h.on_chain_end("not a dict")  # should not raise
        assert len(h.blocks) == 0


class TestTiloCallbackHandlerSpec:
    def test_to_spec_structure(self):
        h = TiloCallbackHandler(run_id="r-abc", title="My Chain")
        h.on_llm_end(_make_llm_response("Result."))
        spec = h.to_spec()
        assert spec["version"] == "tilo/aip/v1"
        assert spec["title"] == "My Chain"
        assert spec["run_id"] == "r-abc"
        assert len(spec["views"]) == 1
        assert spec["views"][0]["id"] == "result"
        assert spec["views"][0]["block_ids"] == [b["id"] for b in spec["blocks"]]

    def test_empty_handler_gives_placeholder(self):
        h = TiloCallbackHandler()
        spec = h.to_spec()
        assert len(spec["blocks"]) == 1
        assert "No output captured." in spec["blocks"][0]["props"]["content"]

    def test_reset_clears_blocks(self):
        h = TiloCallbackHandler()
        h.on_llm_end(_make_llm_response("Something."))
        assert len(h.blocks) == 1
        h.reset()
        assert len(h.blocks) == 0

    def test_reset_allows_reuse(self):
        h = TiloCallbackHandler()
        h.on_llm_end(_make_llm_response("First."))
        h.reset()
        h.on_llm_end(_make_llm_response("Second."))
        spec = h.to_spec()
        assert len(spec["blocks"]) == 1
        assert "Second." in spec["blocks"][0]["props"]["content"]
