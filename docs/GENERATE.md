# Generating & Rendering Surfaces

This is the reference for Tilo's Python API: turning an LLM into an
interactive surface, and rendering it anywhere.

- [`tilo.generate()`](#tilogenerate) — one line, provider auto-detected
- [Provider functions](#provider-functions) — use your own client
- [`AIPPromptBuilder`](#aippromptbuilder) — bring any LLM
- [Skills](#skills) — shape the output for your domain
- [Rendering](#rendering) — browser, Jupyter, HTML, React
- [The spec format](#the-aip-spec) — what comes out

---

## `tilo.generate()`

The simplest entry point. The provider is detected from the model name.

```python
import tilo

spec = tilo.generate(
    goal="Review this SaaS contract for payment and IP risks.",
    model="gpt-4o",            # gpt-* → OpenAI, claude-* → Anthropic
    api_key="sk-...",          # or set OPENAI_API_KEY / ANTHROPIC_API_KEY
    skill="auto",              # "auto" detects; or name a skill explicitly
    document=contract_text,    # optional: a document to ground the surface
    memories=["prefers conservative revisions"],  # optional recalled prefs
    language="en",             # "en" / "zh" to force output language
)
```

Returns a validated `ArtifactSpecV1`. Requires the matching SDK
(`pip install "tilo[openai]"` or `"tilo[anthropic]"`).

| Model prefix | Provider | Install |
|---|---|---|
| `gpt-*`, `o1-*`, `o3-*` | OpenAI | `pip install "tilo[openai]"` |
| `claude-*` | Anthropic | `pip install "tilo[anthropic]"` |

For other providers, use `generate_with_langchain()` or `AIPPromptBuilder`.

---

## Provider functions

Use these when you already have a configured client (custom base URL,
org, proxy, retries, etc.).

```python
from openai import OpenAI
from tilo.generate import generate_with_openai

spec = generate_with_openai(
    OpenAI(),
    "Analyse the Q3 sales pipeline and recommend follow-ups.",
    model="gpt-4o",
    skill="sales_dashboard",
)
```

```python
import anthropic
from tilo.generate import generate_with_anthropic

spec = generate_with_anthropic(
    anthropic.Anthropic(),
    "Review this PR for security issues.",
    model="claude-opus-4-8",
    skill="code_review",
    document=pr_diff,
)
```

```python
from langchain_openai import ChatOpenAI
from tilo.generate import generate_with_langchain

spec = generate_with_langchain(
    ChatOpenAI(model="gpt-4o", temperature=0.3),
    "Plan a 3-day trip to Tokyo.",
    skill="trip_planning",
)
```

The same functions are re-exported from each adapter as `generate_aip_spec()`:

```python
from tilo.adapters.openai import generate_aip_spec
spec = generate_aip_spec(OpenAI(), "...", skill="...")
```

---

## `AIPPromptBuilder`

The prompt-engineering layer. Works with **any** LLM — call your model
yourself and parse the result.

```python
from tilo.prompt import AIPPromptBuilder

builder = AIPPromptBuilder(
    "Summarise this incident and propose remediation.",
    skill="incident_response",
    document=incident_log,
)

# Get the prompts in the shape your client wants:
system = builder.system_prompt()
user   = builder.user_prompt()

messages = builder.messages_openai()       # [{"role": "system", ...}, ...]
kwargs   = builder.messages_anthropic()     # {"system": ..., "messages": ...}
template = builder.messages_langchain()     # ChatPromptTemplate

# Call your LLM, then parse the raw text into a validated spec:
raw = my_llm(messages)
spec_dict = builder.parse(raw)              # None on failure
```

`parse()` is robust: it strips markdown fences, finds the JSON object inside
prose, assigns missing block IDs, prunes view references to non-existent
blocks, and accepts both `props` and legacy `data` keys.

### Custom skills from YAML

```python
builder = AIPPromptBuilder.from_skill_file(
    "Review this RFP response.",
    "my_skills/rfp_review.yaml",
)
```

The YAML matches `skills/*/skill.yaml`:

```yaml
name: rfp-review
block_hints:
  - type: table
    use_when: "Comparing requirements vs. our response"
  - type: chart
    variant: bar
    use_when: "Showing coverage score per section"
view_hints: |
  "Coverage" tab: score chart + requirements table.
  "Gaps" tab: list of unmet requirements + memory_card.
```

---

## Skills

A skill shapes the surface for a domain: which block types to prefer and
how to organise views. Skills are **hints**, not constraints — the LLM still
decides the final layout.

```python
from tilo.prompt import AIPPromptBuilder
print(AIPPromptBuilder.list_skills())
```

| Skill | For |
|---|---|
| `contract_review` | Contract risk, clauses, revisions |
| `code_review` | PR review, diffs, merge gate |
| `sales_dashboard` | Pipeline metrics, follow-ups |
| `trip_planning` | Itineraries, packing, budget |
| `competitive_analysis` | Competitor comparison, strategy |
| `data_analysis` | KPIs, charts, exploration |
| `incident_response` | Post-mortem, timeline, remediation |
| `meeting_summary` | Notes, decisions, action items |
| `bug_report` | Repro steps, root cause, fix verify |
| `document_review` | Section feedback, revisions, approval |
| `research_summary` | Paper findings, methodology, citations |
| `onboarding_plan` | Week-by-week tasks, resources |

`skill="auto"` (the default) detects the best skill from the goal text.
`skill=None` disables hints entirely.

---

## Rendering

A spec is plain JSON — render it however you like.

### Zero-setup (Python only)

```python
tilo.view(spec)                    # opens a temp server in your browser
tilo.notebook(spec)                # inline in Jupyter / Colab
tilo.save_html(spec, "out.html")   # standalone file, no CDN
html = tilo.to_html(spec)          # the HTML string
```

The built-in renderer supports all 20 block types including SVG charts
(bar / radar / pie), diffs, timelines, kanban, and interactive
checklists / ratings / forms — with no JavaScript dependencies.

### Production React

```bash
npm install @adam2go/tilo-react recharts lucide-react
```

```tsx
import { renderArtifactBlock } from "@adam2go/tilo-react";

{spec.blocks.map((b) => <div key={b.id}>{renderArtifactBlock(b)}</div>)}
```

For the live, action-wired experience (surfaces, action callbacks, polling),
use `TiloRenderer` + `useTiloSurface` against a running Tilo backend. See the
[`@adam2go/tilo-react` README](../packages/react/README.md).

### Live playground

```bash
tilo serve
# open http://localhost:8000/playground
```

Paste any spec on the left, see it render instantly on the right.

---

## The AIP spec

`generate()` returns an `ArtifactSpecV1`. As a dict it looks like:

```json
{
  "version": "tilo/aip/v1",
  "title": "Contract Risk Review",
  "status": "ready",
  "blocks": [
    { "id": "h", "type": "heading", "props": { "text": "...", "severity": "high" } },
    { "id": "c", "type": "chart", "props": { "chart_type": "radar", "axes": [...] } },
    { "id": "conf", "type": "confirmation", "props": { "description": "...", "risk_level": "high" } },
    { "id": "mem", "type": "memory_card", "props": { "content": "...", "confidence": 0.85 } }
  ],
  "views": [
    { "id": "v1", "label": "Risks", "block_ids": ["h", "c"] },
    { "id": "v2", "label": "Decision", "block_ids": ["conf", "mem"] }
  ],
  "follow_ups": ["...", "..."]
}
```

See [`docs/AIP_DESIGN.md`](./AIP_DESIGN.md) for the full block-type catalogue
and the design rationale.
