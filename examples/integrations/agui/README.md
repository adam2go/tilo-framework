# Tilo × AG-UI — best practices

[AG-UI](https://docs.ag-ui.com) streams an agent's activity into a chat/copilot
UI (via CopilotKit). Tilo produces a **structured surface** as data. They
compose: **let your AG-UI agent emit a Tilo surface as generative UI**, instead
of streaming a wall of text.

```
Your agent ──AG-UI events──▶ CopilotKit frontend
                │
                └─ CUSTOM "tilo.surface" event  ──▶  @adam2go/tilo-react renders it
```

## The four pieces

| File | What it shows | Runs on |
|---|---|---|
| [`emit_surface.py`](./emit_surface.py) | Tilo surface → AG-UI events (the emit side) | `pip install tilo` |
| [`consume_stream.py`](./consume_stream.py) | AG-UI agent stream → one Tilo surface | `pip install tilo` |
| [`sse_server.py`](./sse_server.py) | A real SSE endpoint streaming AG-UI events | `pip install tilo` |
| [`CopilotKitRenderer.tsx`](./CopilotKitRenderer.tsx) | Render `tilo.surface` in a CopilotKit app | npm |

```bash
python examples/integrations/agui/emit_surface.py     # see the event stream
python examples/integrations/agui/consume_stream.py   # aggregate a stream → surface
python examples/integrations/agui/sse_server.py       # curl -N http://127.0.0.1:8077/agui
```

## Two patterns

### 1. Emit a Tilo surface into your AG-UI stream (recommended)

Your agent already streams AG-UI events. When it has a structured result,
emit it as a Tilo surface instead of prose:

```python
from tilo.adapters.agui import tilo_spec_to_agui_events

spec = tilo.generate("Summarise the Q3 pipeline", model="gpt-4o")
for event in tilo_spec_to_agui_events(spec):
    yield event   # into your existing AG-UI SSE stream
```

The frontend renders the `CUSTOM` "tilo.surface" event with
[`CopilotKitRenderer.tsx`](./CopilotKitRenderer.tsx).

### 2. Aggregate an AG-UI stream into a Tilo surface

Already have an AG-UI agent? Turn its text + tool-call stream into one clean,
render-anywhere artifact:

```python
from tilo.adapters.agui import agui_events_to_tilo_spec

spec = agui_events_to_tilo_spec(events)   # text → markdown, tools → tool_preview
tilo.view(spec)                            # render anywhere, no CopilotKit needed
```

## FastAPI variant of the SSE endpoint

`sse_server.py` uses the stdlib so it runs on the lean install. In production
you'll usually use FastAPI (`pip install "tilo[server]"`):

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import json, tilo
from tilo.adapters.agui import tilo_spec_to_agui_events

app = FastAPI()

@app.get("/agui")
def agui():
    spec = tilo.generate("Summarise the Q3 pipeline", model="gpt-4o")
    def stream():
        for event in tilo_spec_to_agui_events(spec):
            yield f"data: {json.dumps(event)}\n\n"
    return StreamingResponse(stream(), media_type="text/event-stream")
```

## Why this is the right shape

- **You keep your stack.** AG-UI carries events; CopilotKit renders the app.
  Tilo only supplies the *structured view* — no framework swap.
- **One artifact, not a wall of text.** A chart + approval gate + memory card
  beats paragraphs for decisions.
- **Render-anywhere fallback.** The same spec renders with `tilo.view()` in a
  script or notebook when there's no frontend.
