"""Tests for the A2A and ACP protocol adapters."""
from __future__ import annotations

import pytest

from tilo.adapters.a2a import a2a_task_to_spec
from tilo.adapters.acp import acp_message_to_spec
from tilo.schemas.artifact import ArtifactSpecV1


# --------------------------------------------------------------------------- #
# A2A                                                                          #
# --------------------------------------------------------------------------- #

class TestA2A:
    def test_text_part_to_markdown(self):
        task = {"id": "t1", "artifacts": [{"parts": [{"type": "text", "text": "Hello"}]}]}
        spec = a2a_task_to_spec(task)
        assert spec["version"] == "tilo/aip/v1"
        assert spec["blocks"][0]["type"] == "markdown"
        assert "Hello" in spec["blocks"][0]["props"]["content"]

    def test_data_part_metrics(self):
        task = {"id": "t", "artifacts": [{"parts": [{"type": "data", "data": {"revenue": 1000, "deals": 5}}]}]}
        spec = a2a_task_to_spec(task)
        assert any(b["type"] == "metric" for b in spec["blocks"])

    def test_data_part_table(self):
        task = {"id": "t", "artifacts": [{"parts": [
            {"type": "data", "data": [{"name": "A", "v": "1"}, {"name": "B", "v": "2"}]}]}]}
        spec = a2a_task_to_spec(task)
        assert any(b["type"] == "table" for b in spec["blocks"])

    def test_file_part_to_card(self):
        task = {"id": "t", "artifacts": [{"parts": [
            {"type": "file", "file": {"name": "report.pdf", "uri": "https://x/r.pdf", "mimeType": "application/pdf"}}]}]}
        spec = a2a_task_to_spec(task)
        card = next(b for b in spec["blocks"] if b["type"] == "card")
        assert card["title"] == "report.pdf"
        assert card["props"]["uri"] == "https://x/r.pdf"

    def test_status_message_fallback(self):
        task = {"id": "t", "status": {"state": "completed", "message": {"parts": [{"type": "text", "text": "Done"}]}}}
        spec = a2a_task_to_spec(task)
        assert any("Done" in b["props"].get("content", "") for b in spec["blocks"])

    def test_output_fallback(self):
        task = {"id": "t", "output": "plain output"}
        spec = a2a_task_to_spec(task)
        assert "plain output" in spec["blocks"][0]["props"]["content"]

    def test_empty_task_gives_placeholder(self):
        spec = a2a_task_to_spec({"id": "t"})
        assert "No output" in spec["blocks"][0]["props"]["content"]

    def test_title_from_state(self):
        spec = a2a_task_to_spec({"id": "t", "status": {"state": "working"}})
        assert "working" in spec["title"]

    def test_provenance(self):
        spec = a2a_task_to_spec({"id": "task-42"})
        assert spec["provenance"][0]["type"] == "a2a_task"
        assert spec["provenance"][0]["id"] == "task-42"

    def test_multiple_artifacts_and_parts(self):
        task = {"id": "t", "artifacts": [
            {"parts": [{"type": "text", "text": "A"}, {"type": "text", "text": "B"}]},
            {"parts": [{"type": "text", "text": "C"}]},
        ]}
        spec = a2a_task_to_spec(task)
        contents = [b["props"]["content"] for b in spec["blocks"]]
        assert "A" in contents and "B" in contents and "C" in contents

    def test_kind_alias_for_type(self):
        # Newer A2A drafts use "kind" instead of "type"
        task = {"id": "t", "artifacts": [{"parts": [{"kind": "text", "text": "via kind"}]}]}
        spec = a2a_task_to_spec(task)
        assert "via kind" in spec["blocks"][0]["props"]["content"]

    def test_view_references_all_blocks(self):
        spec = a2a_task_to_spec({"id": "t", "artifacts": [{"parts": [{"type": "text", "text": "x"}]}]})
        assert set(spec["views"][0]["block_ids"]) == {b["id"] for b in spec["blocks"]}

    def test_schema_valid(self):
        task = {"id": "t", "artifacts": [{"parts": [
            {"type": "text", "text": "Summary"},
            {"type": "data", "data": {"score": 9}}]}]}
        spec = a2a_task_to_spec(task)
        ArtifactSpecV1.model_validate(spec)


# --------------------------------------------------------------------------- #
# ACP                                                                          #
# --------------------------------------------------------------------------- #

class TestACP:
    def test_text_part_to_markdown(self):
        msg = {"id": "m1", "parts": [{"content_type": "text/plain", "content": "Hi there"}]}
        spec = acp_message_to_spec(msg)
        assert spec["blocks"][0]["type"] == "markdown"
        assert "Hi there" in spec["blocks"][0]["props"]["content"]

    def test_markdown_content_type(self):
        msg = {"id": "m", "parts": [{"content_type": "text/markdown", "content": "# Title"}]}
        spec = acp_message_to_spec(msg)
        assert spec["blocks"][0]["type"] == "markdown"

    def test_json_object_to_metrics(self):
        msg = {"id": "m", "parts": [{"content_type": "application/json", "content": {"a": 1, "b": 2}}]}
        spec = acp_message_to_spec(msg)
        assert any(b["type"] == "metric" for b in spec["blocks"])

    def test_json_string_parsed(self):
        msg = {"id": "m", "parts": [{"content_type": "application/json", "content": '{"score": 95}'}]}
        spec = acp_message_to_spec(msg)
        assert any(b["type"] == "metric" for b in spec["blocks"])

    def test_json_array_to_table(self):
        msg = {"id": "m", "parts": [{"content_type": "application/json",
                                     "content": [{"n": "A", "v": "1"}, {"n": "B", "v": "2"}]}]}
        spec = acp_message_to_spec(msg)
        assert any(b["type"] == "table" for b in spec["blocks"])

    def test_image_to_card(self):
        msg = {"id": "m", "parts": [{"content_type": "image/png", "content_url": "https://x/i.png", "name": "chart"}]}
        spec = acp_message_to_spec(msg)
        card = next(b for b in spec["blocks"] if b["type"] == "card")
        assert card["props"]["uri"] == "https://x/i.png"
        assert card["props"]["mime_type"] == "image/png"

    def test_unknown_content_type_to_card(self):
        msg = {"id": "m", "parts": [{"content_type": "application/octet-stream", "content": "binary"}]}
        spec = acp_message_to_spec(msg)
        assert any(b["type"] == "card" for b in spec["blocks"])

    def test_camelcase_content_type(self):
        msg = {"id": "m", "parts": [{"contentType": "text/plain", "content": "camel"}]}
        spec = acp_message_to_spec(msg)
        assert "camel" in spec["blocks"][0]["props"]["content"]

    def test_legacy_body(self):
        msg = {"id": "m", "subject": "Hi", "body": "legacy body text"}
        spec = acp_message_to_spec(msg)
        assert "legacy body text" in spec["blocks"][0]["props"]["content"]

    def test_empty_message_placeholder(self):
        spec = acp_message_to_spec({"id": "m"})
        assert "No content" in spec["blocks"][0]["props"]["content"]

    def test_title_from_subject(self):
        spec = acp_message_to_spec({"id": "m", "subject": "Quarterly Update", "body": "x"})
        assert spec["title"] == "Quarterly Update"

    def test_title_from_role(self):
        spec = acp_message_to_spec({"id": "m", "role": "agent", "parts": [{"content_type": "text/plain", "content": "x"}]})
        assert "agent" in spec["title"]

    def test_provenance(self):
        spec = acp_message_to_spec({"id": "msg-7", "body": "x"})
        assert spec["provenance"][0]["type"] == "acp_message"
        assert spec["provenance"][0]["id"] == "msg-7"

    def test_multiple_parts(self):
        msg = {"id": "m", "parts": [
            {"content_type": "text/plain", "content": "intro"},
            {"content_type": "application/json", "content": {"k": 1}},
        ]}
        spec = acp_message_to_spec(msg)
        types = {b["type"] for b in spec["blocks"]}
        assert "markdown" in types and "metric" in types

    def test_schema_valid(self):
        msg = {"id": "m", "parts": [
            {"content_type": "text/plain", "content": "Summary"},
            {"content_type": "application/json", "content": {"score": 9}}]}
        spec = acp_message_to_spec(msg)
        ArtifactSpecV1.model_validate(spec)
