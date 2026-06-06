"""AG-UI ↔ Tilo interop adapter.

[AG-UI](https://docs.ag-ui.com) is an event-streaming protocol: an agent
backend streams JSON events (text deltas, tool calls, state, lifecycle) to a
frontend runtime such as CopilotKit. Tilo is complementary, not competing —
a Tilo surface is a self-contained declarative spec. This adapter bridges the
two so you can:

1. EMIT a Tilo surface into an AG-UI stream (render it as generative UI in a
   CopilotKit app):

    from tilo.adapters.agui import tilo_spec_to_agui_events

    events = tilo_spec_to_agui_events(spec, thread_id="t1", run_id="r1")
    # stream these as your AG-UI run; a client renders the CUSTOM
    # "tilo.surface" event with @adam2go/tilo-react.

2. CONSUME an AG-UI event stream and render it as a structured Tilo surface:

    from tilo.adapters.agui import agui_events_to_tilo_spec

    spec = agui_events_to_tilo_spec(events, title="Agent Result")
    # → text deltas become markdown, tool calls become tool_preview,
    #   a CUSTOM "tilo.surface" event round-trips its embedded spec.

The adapter matches AG-UI's SCREAMING_SNAKE event ``type`` values and is
graceful about PascalCase variants and camelCase field names.
"""

from __future__ import annotations

import json
from typing import Any

SURFACE_EVENT_NAME = "tilo.surface"


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

def _event_type(event: dict[str, Any]) -> str:
    """Normalise an AG-UI event type to SCREAMING_SNAKE."""
    raw = str(event.get("type", ""))
    # Accept PascalCase (e.g. "TextMessageContent") and convert.
    if raw and "_" not in raw and not raw.isupper():
        out = []
        for i, ch in enumerate(raw):
            if ch.isupper() and i > 0:
                out.append("_")
            out.append(ch.upper())
        return "".join(out)
    return raw.upper()


def _to_dict(spec: Any) -> dict[str, Any]:
    if isinstance(spec, dict):
        return spec
    if hasattr(spec, "model_dump"):
        return spec.model_dump()
    if isinstance(spec, str):
        return json.loads(spec)
    raise TypeError(f"Cannot convert {type(spec)} to a spec dict")


# --------------------------------------------------------------------------- #
# EMIT: Tilo spec → AG-UI events                                              #
# --------------------------------------------------------------------------- #

def tilo_spec_to_agui_events(
    spec: Any,
    *,
    thread_id: str = "tilo-thread",
    run_id: str = "tilo-run",
    lifecycle: bool = True,
) -> list[dict[str, Any]]:
    """Emit a Tilo AIP spec as a sequence of AG-UI protocol events.

    The surface is carried in a ``CUSTOM`` event named ``"tilo.surface"`` —
    AG-UI's extension point for application-defined / generative UI. A client
    (e.g. CopilotKit) renders it with ``@adam2go/tilo-react``.

    Args:
        spec:       An ``ArtifactSpecV1`` instance, a dict, or a JSON string.
        thread_id:  AG-UI thread id (for the run lifecycle events).
        run_id:     AG-UI run id.
        lifecycle:  Wrap the CUSTOM event in RUN_STARTED / RUN_FINISHED
                    (set False to emit only the CUSTOM event).

    Returns:
        A list of AG-UI event dicts, ready to stream.
    """
    spec_dict = _to_dict(spec)
    custom = {"type": "CUSTOM", "name": SURFACE_EVENT_NAME, "value": spec_dict}
    if not lifecycle:
        return [custom]
    return [
        {"type": "RUN_STARTED", "threadId": thread_id, "runId": run_id},
        custom,
        {"type": "RUN_FINISHED", "threadId": thread_id, "runId": run_id},
    ]


# --------------------------------------------------------------------------- #
# CONSUME: AG-UI events → Tilo spec                                           #
# --------------------------------------------------------------------------- #

def agui_events_to_tilo_spec(
    events: list[dict[str, Any]],
    *,
    title: str = "Agent Result",
    run_id: str | None = None,
) -> dict[str, Any]:
    """Aggregate an AG-UI event stream into a Tilo AIP v1 spec.

    Mapping:
        CUSTOM "tilo.surface"  → returned directly (round-trips an embedded spec)
        TEXT_MESSAGE_CONTENT   → markdown block (accumulated per messageId)
        TOOL_CALL_START/ARGS   → tool_preview block (name + accumulated args)
        TOOL_CALL_RESULT       → tool_preview output
        STATE_SNAPSHOT         → a "tilo.surface" snapshot round-trips; else JSON

    Args:
        events: A list of AG-UI event dicts.
        title:  Spec title when one isn't embedded.
        run_id: Optional run id for provenance.

    Returns:
        A Tilo AIP v1 spec dict.
    """
    blocks: list[dict[str, Any]] = []
    texts: dict[str, str] = {}            # messageId → accumulated text
    text_order: list[str] = []
    tools: dict[str, dict[str, str]] = {}  # toolCallId → {name, args, result}
    tool_order: list[str] = []

    for event in events:
        etype = _event_type(event)

        if etype == "CUSTOM" and event.get("name") == SURFACE_EVENT_NAME:
            # A surface was embedded directly — round-trip it.
            value = event.get("value")
            if isinstance(value, dict) and value.get("blocks"):
                return value

        elif etype in ("TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_CHUNK"):
            mid = str(event.get("messageId", "msg"))
            if mid not in texts:
                texts[mid] = ""
                text_order.append(mid)
            texts[mid] += str(event.get("delta", "") or "")

        elif etype in ("TOOL_CALL_START", "TOOL_CALL_CHUNK"):
            tid = str(event.get("toolCallId", "tool"))
            if tid not in tools:
                tools[tid] = {"name": "", "args": "", "result": ""}
                tool_order.append(tid)
            name = event.get("toolCallName") or event.get("toolName") or ""
            tools[tid]["name"] = tools[tid]["name"] or str(name)
            tools[tid]["args"] += str(event.get("delta", "") or "")

        elif etype == "TOOL_CALL_ARGS":
            tid = str(event.get("toolCallId", "tool"))
            tools.setdefault(tid, {"name": "", "args": "", "result": ""})
            if tid not in tool_order:
                tool_order.append(tid)
            tools[tid]["args"] += str(event.get("delta", "") or "")

        elif etype == "TOOL_CALL_RESULT":
            tid = str(event.get("toolCallId", "tool"))
            tools.setdefault(tid, {"name": "", "args": "", "result": ""})
            if tid not in tool_order:
                tool_order.append(tid)
            tools[tid]["result"] = str(event.get("content", "") or "")

        elif etype == "STATE_SNAPSHOT":
            snapshot = event.get("snapshot")
            if isinstance(snapshot, dict) and snapshot.get("blocks"):
                return snapshot

    # Build blocks in arrival order: texts first, then tools.
    for mid in text_order:
        content = texts[mid].strip()
        if content:
            blocks.append({
                "id": f"agui_{mid}",
                "type": "markdown",
                "props": {"content": content},
            })

    for tid in tool_order:
        tc = tools[tid]
        output = tc["result"] or tc["args"]
        blocks.append({
            "id": f"agui_{tid}",
            "type": "tool_preview",
            "title": tc["name"] or "tool",
            "props": {
                "tool_name": tc["name"] or "tool",
                "status": "success" if tc["result"] else "pending",
                "output": output[:2000],
            },
        })

    if not blocks:
        blocks.append({
            "id": "agui_empty",
            "type": "markdown",
            "props": {"content": "No renderable content in the AG-UI stream."},
        })

    spec: dict[str, Any] = {
        "version": "tilo/aip/v1",
        "title": title,
        "status": "ready",
        "blocks": blocks,
        "views": [{"id": "result", "label": "Result", "block_ids": [b["id"] for b in blocks]}],
        "actions": [],
        "provenance": [{"type": "agui_stream", "id": run_id or "agui"}],
        "memory_refs": [],
        "follow_ups": [],
    }
    return spec
