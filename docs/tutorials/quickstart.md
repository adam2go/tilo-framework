# Tilo in 5 Minutes

From zero to a renderable AI-generated surface — no Docker, no setup beyond `pip install`.

---

## Prerequisites

- Python 3.11+
- Node.js 18+ (for the React renderer, optional)

---

## Step 1 — Install and scaffold

```bash
pip install tilo
tilo init my-agent
cd my-agent
```

This creates:

```
my-agent/
├── .env              # SQLite by default, no Docker needed
├── requirements.txt
├── hello.py          # end-to-end demo script
├── openai_agent.py   # LLM integration example
└── README.md
```

---

## Step 2 — Start the server

```bash
tilo serve
```

Expected output:

```
▶  Tilo API  →  http://127.0.0.1:8000
   Health     →  http://127.0.0.1:8000/api/health
   API docs   →  http://127.0.0.1:8000/docs
```

Tilo uses SQLite by default. No database setup needed.

---

## Step 3 — Run the demo

In a **new terminal**:

```bash
python hello.py
```

Expected output:

```
Session: <uuid>

Run status: completed

Artifact: Contract Review
Blocks:   5
  · [heading]  {'text': 'Contract Risk Analysis'}
  · [markdown] {'content': 'Found 2 high-risk clauses...'}
  · [metric]   {'label': 'Risk Level', 'value': 'High'}

Render with @adam2go/tilo-react:
  import { renderArtifactBlock } from '@adam2go/tilo-react'
  · [card]     ...
```

You've just run the full **ROAM loop**: Render → Observe → Act → Memorize.

---

## Step 4 — Render in React

```bash
npm install @adam2go/tilo-react recharts lucide-react
```

```tsx
import { TiloRenderer, createTiloClient, useTiloSurface } from "@adam2go/tilo-react";

const client = createTiloClient({ baseUrl: "http://localhost:8000" });

function AgentSurface({ runId }: { runId: string }) {
  const { turns, loading } = useTiloSurface({ client, runId });

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      {turns.map((turn) => (
        <TiloRenderer
          key={turn.id}
          surface={turn.spec}
          onAction={async (event) => {
            await client.executeSurfaceAction({
              surface: turn.spec,
              actionId: event.action.id,
              workspaceId: "my-workspace",
              runId,
            });
          }}
        />
      ))}
    </div>
  );
}
```

---

## Step 5 — Connect your LLM

### With OpenAI

```bash
pip install openai
export OPENAI_API_KEY=sk-...
```

```python
from openai import OpenAI
from tilo.adapters.openai import tilo_spec_from_completion

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Analyse this contract for payment risks."}],
)
spec = tilo_spec_from_completion(response, title="Contract Analysis")
# → spec is a Tilo AIP v1 dict, ready to render
```

### With Anthropic

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

```python
import anthropic
from tilo.adapters.anthropic_sdk import tilo_spec_from_message

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Review this contract."}],
)
spec = tilo_spec_from_message(response, title="Contract Review")
```

### With LangChain

```bash
pip install langchain-openai langchain-core
```

```python
from langchain_openai import ChatOpenAI
from tilo.adapters.langchain import TiloCallbackHandler

handler = TiloCallbackHandler(title="My Agent")
llm = ChatOpenAI(model="gpt-4o")
llm.invoke("Analyse this contract.", config={"callbacks": [handler]})
spec = handler.to_spec()
```

---

## What you built

```
Your code        LLM response        Tilo adapter        AIP spec
─────────────    ─────────────────   ─────────────────   ──────────────────────
openai call   →  ChatCompletion   →  tilo_spec_from_  →  {version, blocks, views}
anthropic call→  Message          →  completion()     →     ↓
langchain call→  AIMessage        →  tilo_spec_from_  →  @adam2go/tilo-react
                                     message()           renderArtifactBlock(block)
```

---

## What's automatic

| LLM output | Tilo block |
|---|---|
| Plain text | `markdown` |
| JSON `{"key": value}` with ≤8 entries | `metric` blocks |
| JSON array of objects | `table` |
| Tool call / tool_use | `tool_preview` |

---

## Next steps

- [`examples/integrations/`](../../examples/integrations/) — full working examples for each LLM provider
- [`docs/AIP_DESIGN.md`](../AIP_DESIGN.md) — Agent Interaction Protocol spec
- [`docs/INTEGRATION_GUIDE.md`](../INTEGRATION_GUIDE.md) — advanced integration modes
- [npm: @adam2go/tilo-react](https://www.npmjs.com/package/@adam2go/tilo-react) — React renderer
- [PyPI: tilo](https://pypi.org/project/tilo/) — Python backend
