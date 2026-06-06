"""AG-UI best practice #3 — a real SSE endpoint that streams a Tilo surface.

This is the wire format an AG-UI client (CopilotKit) connects to: a Server-Sent
Events stream of AG-UI protocol events. Here the "agent" generates a Tilo
surface and streams it as a CUSTOM "tilo.surface" event.

Uses only the Python standard library, so it runs on the lean install
(`pip install tilo`) with no FastAPI required.

    python examples/integrations/agui/sse_server.py
    # then:  curl -N http://127.0.0.1:8077/agui

A FastAPI version (what most production AG-UI backends use) is in the README.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from tilo.adapters.agui import tilo_spec_to_agui_events

SURFACE = {
    "version": "tilo/aip/v1",
    "title": "Incident Summary",
    "status": "ready",
    "blocks": [
        {"id": "h", "type": "heading", "props": {"text": "API latency incident — resolved", "severity": "medium"}},
        {"id": "tl", "type": "timeline", "props": {"items": [
            {"time": "09:12", "title": "Detected", "description": "p99 latency > 2s"},
            {"time": "09:31", "title": "Resolved", "description": "rolled back deploy"}]}},
        {"id": "mem", "type": "memory_card", "props": {"content": "Page primary on-call first", "confidence": 0.7}},
    ],
    "views": [{"id": "v", "label": "Incident", "block_ids": ["h", "tl", "mem"]}],
    "follow_ups": ["Draft the post-mortem"],
}


class AGUIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/agui":
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        # Stream each AG-UI event as an SSE `data:` frame.
        for event in tilo_spec_to_agui_events(SURFACE, thread_id="ops", run_id="inc-42"):
            self.wfile.write(f"data: {json.dumps(event)}\n\n".encode())
            self.wfile.flush()

    def log_message(self, *args):
        pass


def main() -> None:
    server = HTTPServer(("127.0.0.1", 8077), AGUIHandler)
    print("AG-UI SSE endpoint → http://127.0.0.1:8077/agui")
    print("Try:  curl -N http://127.0.0.1:8077/agui")
    print("(Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
