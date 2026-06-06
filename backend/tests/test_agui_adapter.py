"""Tests for the AG-UI ↔ Tilo interop adapter."""
from __future__ import annotations

import pytest

from tilo.adapters.agui import (
    SURFACE_EVENT_NAME,
    agui_events_to_tilo_spec,
    tilo_spec_to_agui_events,
)
from tilo.schemas.artifact import ArtifactSpecV1


def _spec() -> dict:
    return {
        "version": "tilo/aip/v1", "title": "Risk Review", "status": "ready",
        "blocks": [{"id": "b", "type": "heading", "props": {"text": "Hi", "severity": "info"}}],
        "views": [{"id": "v", "label": "V", "block_ids": ["b"]}],
        "follow_ups": [],
    }


# --------------------------------------------------------------------------- #
# EMIT: spec → AG-UI events                                                    #
# --------------------------------------------------------------------------- #

class TestEmit:
    def test_emits_custom_surface_event_with_lifecycle(self):
        events = tilo_spec_to_agui_events(_spec(), thread_id="t1", run_id="r1")
        types = [e["type"] for e in events]
        assert types == ["RUN_STARTED", "CUSTOM", "RUN_FINISHED"]
        custom = events[1]
        assert custom["name"] == SURFACE_EVENT_NAME
        assert custom["value"]["title"] == "Risk Review"

    def test_lifecycle_false_emits_only_custom(self):
        events = tilo_spec_to_agui_events(_spec(), lifecycle=False)
        assert len(events) == 1
        assert events[0]["type"] == "CUSTOM"

    def test_run_and_thread_ids_propagate(self):
        events = tilo_spec_to_agui_events(_spec(), thread_id="abc", run_id="xyz")
        assert events[0]["threadId"] == "abc"
        assert events[0]["runId"] == "xyz"

    def test_accepts_pydantic_model(self):
        model = ArtifactSpecV1.model_validate(_spec())
        events = tilo_spec_to_agui_events(model)
        assert events[1]["value"]["title"] == "Risk Review"


# --------------------------------------------------------------------------- #
# CONSUME: AG-UI events → spec                                                 #
# --------------------------------------------------------------------------- #

class TestConsume:
    def test_text_messages_become_markdown(self):
        events = [
            {"type": "TEXT_MESSAGE_START", "messageId": "m1", "role": "assistant"},
            {"type": "TEXT_MESSAGE_CONTENT", "messageId": "m1", "delta": "Hello "},
            {"type": "TEXT_MESSAGE_CONTENT", "messageId": "m1", "delta": "world."},
            {"type": "TEXT_MESSAGE_END", "messageId": "m1"},
        ]
        spec = agui_events_to_tilo_spec(events)
        md = [b for b in spec["blocks"] if b["type"] == "markdown"]
        assert len(md) == 1
        assert "Hello world." in md[0]["props"]["content"]

    def test_tool_calls_become_tool_preview(self):
        events = [
            {"type": "TOOL_CALL_START", "toolCallId": "t1", "toolCallName": "search"},
            {"type": "TOOL_CALL_ARGS", "toolCallId": "t1", "delta": '{"q":"tilo"}'},
            {"type": "TOOL_CALL_END", "toolCallId": "t1"},
            {"type": "TOOL_CALL_RESULT", "toolCallId": "t1", "content": "3 results"},
        ]
        spec = agui_events_to_tilo_spec(events)
        tools = [b for b in spec["blocks"] if b["type"] == "tool_preview"]
        assert len(tools) == 1
        assert tools[0]["props"]["tool_name"] == "search"
        assert tools[0]["props"]["status"] == "success"
        assert "3 results" in tools[0]["props"]["output"]

    def test_pending_tool_when_no_result(self):
        events = [
            {"type": "TOOL_CALL_START", "toolCallId": "t1", "toolCallName": "calc"},
            {"type": "TOOL_CALL_ARGS", "toolCallId": "t1", "delta": "1+1"},
        ]
        spec = agui_events_to_tilo_spec(events)
        tool = next(b for b in spec["blocks"] if b["type"] == "tool_preview")
        assert tool["props"]["status"] == "pending"
        assert "1+1" in tool["props"]["output"]

    def test_custom_surface_event_round_trips(self):
        original = _spec()
        events = tilo_spec_to_agui_events(original)
        spec = agui_events_to_tilo_spec(events)
        assert spec["title"] == "Risk Review"
        assert spec["blocks"][0]["type"] == "heading"

    def test_state_snapshot_with_surface_round_trips(self):
        events = [{"type": "STATE_SNAPSHOT", "snapshot": _spec()}]
        spec = agui_events_to_tilo_spec(events)
        assert spec["title"] == "Risk Review"

    def test_mixed_text_and_tools(self):
        events = [
            {"type": "TEXT_MESSAGE_CONTENT", "messageId": "m1", "delta": "Found issues:"},
            {"type": "TOOL_CALL_START", "toolCallId": "t1", "toolCallName": "lookup"},
            {"type": "TOOL_CALL_RESULT", "toolCallId": "t1", "content": "data"},
        ]
        spec = agui_events_to_tilo_spec(events)
        types = {b["type"] for b in spec["blocks"]}
        assert "markdown" in types and "tool_preview" in types

    def test_pascalcase_event_types_accepted(self):
        events = [
            {"type": "TextMessageContent", "messageId": "m1", "delta": "camel case"},
        ]
        spec = agui_events_to_tilo_spec(events)
        assert "camel case" in spec["blocks"][0]["props"]["content"]

    def test_empty_stream_gives_placeholder(self):
        spec = agui_events_to_tilo_spec([])
        assert "No renderable content" in spec["blocks"][0]["props"]["content"]

    def test_provenance_set(self):
        spec = agui_events_to_tilo_spec([], run_id="run-9")
        assert spec["provenance"][0]["type"] == "agui_stream"
        assert spec["provenance"][0]["id"] == "run-9"

    def test_output_is_schema_valid(self):
        events = [
            {"type": "TEXT_MESSAGE_CONTENT", "messageId": "m1", "delta": "Summary"},
            {"type": "TOOL_CALL_START", "toolCallId": "t1", "toolCallName": "search"},
            {"type": "TOOL_CALL_RESULT", "toolCallId": "t1", "content": "ok"},
        ]
        spec = agui_events_to_tilo_spec(events)
        ArtifactSpecV1.model_validate(spec)


# --------------------------------------------------------------------------- #
# Round-trip                                                                   #
# --------------------------------------------------------------------------- #

class TestRoundTrip:
    def test_spec_to_events_to_spec_preserves_blocks(self):
        original = ArtifactSpecV1.model_validate({
            "version": "tilo/aip/v1", "title": "Pipeline", "status": "ready",
            "blocks": [
                {"id": "m", "type": "metric", "props": {"label": "Deals", "value": "12"}},
                {"id": "c", "type": "confirmation", "props": {"description": "Send?", "risk_level": "high"}},
            ],
            "views": [{"id": "v", "label": "V", "block_ids": ["m", "c"]}],
            "follow_ups": ["next"],
        })
        events = tilo_spec_to_agui_events(original)
        back = agui_events_to_tilo_spec(events)
        assert [b["type"] for b in back["blocks"]] == ["metric", "confirmation"]
        assert back["title"] == "Pipeline"
