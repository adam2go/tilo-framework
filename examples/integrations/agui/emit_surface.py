"""AG-UI best practice #1 — emit a Tilo surface into an AG-UI stream.

Pattern: your agent already speaks AG-UI (to a CopilotKit frontend). Instead of
streaming a wall of text, have it emit a *structured Tilo surface* as a CUSTOM
"tilo.surface" event — AG-UI's extension point for generative UI. The frontend
renders it with @adam2go/tilo-react (see CopilotKitRenderer.tsx).

Runs on the lean install (`pip install tilo`) — no API key, no server needed.

    python examples/integrations/agui/emit_surface.py
"""

from __future__ import annotations

import json

import tilo
from tilo.adapters.agui import tilo_spec_to_agui_events


def build_surface() -> dict:
    """In a real agent this is `tilo.generate(goal, model=...)`."""
    return {
        "version": "tilo/aip/v1",
        "title": "Q3 Pipeline Review",
        "status": "ready",
        "blocks": [
            {"id": "m1", "type": "metric", "props": {"label": "Hot Accounts", "value": "12", "delta": "+3"}},
            {"id": "m2", "type": "metric", "props": {"label": "Projected", "value": "$1.4M"}},
            {"id": "chart", "type": "chart", "title": "Pipeline by Stage",
             "props": {"chart_type": "bar", "axes": [
                 {"label": "Lead", "score": 40}, {"label": "Qual", "score": 25},
                 {"label": "Demo", "score": 15}, {"label": "Close", "score": 8}]}},
            {"id": "cl", "type": "checklist", "props": {"items": [
                {"text": "Follow up with Acme (stalled 14d)", "checked": False},
                {"text": "Send proposal to Globex"}]}},
            {"id": "conf", "type": "confirmation",
             "props": {"description": "Send the 3 drafted follow-up emails?", "risk_level": "medium"}},
            {"id": "mem", "type": "memory_card",
             "props": {"content": "User prioritises deals by stall time, not size", "confidence": 0.8}},
        ],
        "views": [
            {"id": "v1", "label": "Pipeline", "block_ids": ["m1", "m2", "chart"]},
            {"id": "v2", "label": "Actions", "block_ids": ["cl", "conf", "mem"]},
        ],
        "follow_ups": ["Draft the Acme follow-up", "Compare to Q2 pipeline"],
    }


def main() -> None:
    spec = build_surface()

    # Convert the surface into AG-UI protocol events.
    events = tilo_spec_to_agui_events(spec, thread_id="sales-thread", run_id="run-q3")

    print("AG-UI event stream (what your backend streams to the client):\n")
    for event in events:
        # AG-UI is typically transported as SSE: one `data:` frame per event.
        print(f"data: {json.dumps(event)}\n")

    print("─" * 60)
    print("The CUSTOM 'tilo.surface' event carries the full spec; a CopilotKit")
    print("client renders it with renderArtifactBlock() — see CopilotKitRenderer.tsx.")

    # Sanity: a client could also reconstruct the surface and render it anywhere.
    from tilo.adapters.agui import agui_events_to_tilo_spec
    rebuilt = agui_events_to_tilo_spec(events)
    tilo.save_html(rebuilt, "/tmp/agui_emitted_surface.html")
    print("\nSaved a standalone render to /tmp/agui_emitted_surface.html")


if __name__ == "__main__":
    main()
