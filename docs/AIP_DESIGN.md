# Agent Interaction Protocol (AIP) — Design Document

> Status: **Draft** · Created: 2025-05-14 · Author: Core Team

---

## 1. Problem Statement

Tilo v0.x implemented artifact blocks as a closed, pre-defined set (26 types). This creates three adoption barriers:

1. **Integration cost** — Developers using LangChain, CrewAI, AutoGen or other agent frameworks must rewrite output logic to emit Tilo-specific block types.
2. **Protocol mismatch** — MCP returns `TextContent / ImageContent / EmbeddedResource`; ACP and A2A have their own message schemas. None of them map 1:1 to Tilo's block vocabulary.
3. **Extension friction** — Adding a domain-specific block (e.g. `gantt_chart`, `medical_report`) requires changes in backend schema + backend spec builder + frontend renderer — a full-stack invasive edit across ~60 files.

Meanwhile, the landscape already has well-defined protocols for **tool calling** (MCP), **agent communication** (ACP / A2A), and **agent orchestration** (LangGraph, CrewAI). What is **missing** is a standard for:

> How does an Agent's output become an interactive, confirmable, memorable UI?

This is the gap Tilo should own.

---

## 2. Positioning

```
MCP  → Agent's hands  (how agents call tools)
ACP  → Agent's mouth  (how agents talk to each other)
A2A  → Agent's address book  (how agents discover each other)
Tilo → Agent's face   (how agent output becomes interactive UI)
```

Tilo is an **Agent Interaction Protocol (AIP)**: a declarative spec that turns agent output into interactive surfaces with built-in support for confirmation, memory, and traceability.

### What Tilo is

| Capability | Description |
|------------|-------------|
| **Spec Layer** | A JSON schema defining views, blocks, confirmations, memory candidates, and follow-ups |
| **Runtime** | Memory engine, confirmation inbox, trace recorder |
| **SDK** | Renderer libraries for multiple frontend frameworks |
| **Adapters** | Bridges from MCP / ACP / LangChain / etc. into Tilo spec |
| **Reference UI** | An official Next.js implementation |

### What Tilo is NOT

- Not an agent orchestration framework (use LangChain/LangGraph/CrewAI)
- Not a tool-calling protocol (use MCP)
- Not an agent communication protocol (use ACP/A2A)
- Not a frontend component library (renderers are pluggable)

---

## 3. Architecture Layers

```
┌──────────────────────────────────────────────────────────────┐
│  Layer 4: Skill Hints + LLM-driven Composition               │
│  Skills provide block-type hints & view recommendations       │
│  LLM dynamically decides views, blocks, layout               │
├──────────────────────────────────────────────────────────────┤
│  Layer 3: Renderer SDKs (frontend-agnostic)                   │
│  @tilo/react  ·  @tilo/vue  ·  @tilo/web-components          │
│  Developers can override any block renderer                   │
├──────────────────────────────────────────────────────────────┤
│  Layer 2: Protocol Adapters                                   │
│  mcp_adapter   → MCP Content       → Tilo blocks             │
│  acp_adapter   → ACP messages      → Tilo spec               │
│  a2a_adapter   → A2A task results  → Tilo spec               │
│  lc_adapter    → LangChain output  → Tilo spec               │
│  raw_adapter   → arbitrary JSON    → generic blocks           │
├──────────────────────────────────────────────────────────────┤
│  Layer 1: Core Spec + Runtime                                 │
│  ~20 primitive block types (like HTML tags)                   │
│  Memory engine · Confirmation inbox · Trace recorder          │
│  Declarative JSON spec: views + blocks + actions              │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Core Spec (Layer 1)

### 4.1 Primitive Block Types

Inspired by HTML's semantic elements, these cover ~95% of agent output scenarios. **This set should be stable and rarely changed.**

#### Content Display

| Type | HTML Analogy | Description |
|------|-------------|-------------|
| `markdown` | `<article>` | Rich text, the universal fallback |
| `table` | `<table>` | Columns + rows |
| `list` | `<ul>/<ol>` | Ordered or unordered items |
| `image` | `<img>` | Image with alt text |
| `video` | `<video>` | Embedded video |
| `code` | `<pre><code>` | Code block with language hint |
| `heading` | `<h1>-<h6>` | Section heading |

#### Data Visualization

| Type | Description |
|------|-------------|
| `metric` | Single KPI value (label + value + trend) |
| `chart` | Visualization — `props.chart_type` controls variant (line, bar, pie, radar, etc.) |
| `progress` | Progress bar / step indicator |

#### User Interaction

| Type | Description |
|------|-------------|
| `form` | Input fields + submit |
| `button_group` | Action buttons |

#### Structured Display

| Type | Description |
|------|-------------|
| `card` | Generic container with title, content, optional actions |
| `diff` | Before/after comparison |
| `timeline` | Chronological sequence |
| `kanban` | Column-based board |
| `tabs` | Nested tab group (view-in-view) |

#### Tilo-native (framework-specific)

| Type | Description |
|------|-------------|
| `confirmation` | Action requiring human approval |
| `memory_card` | Memory candidate display |
| `tool_preview` | Tool call preview with approve/reject |

**Total: ~20 types.** Any type not in this set falls back to `generic` (renders as JSON viewer with type badge).

### 4.2 Block Schema

```jsonc
{
  "id": "string",          // unique within artifact
  "type": "string",        // one of the primitives, or any custom string
  "props": {},             // type-specific properties (replaces "data")
  "actions": [],           // optional interactive actions
  "state_binding": null    // optional binding to runtime state
}
```

Key change from v0.x: `data` → `props` to align with component-model conventions (React props, Web Component properties).

### 4.3 View Schema

```jsonc
{
  "id": "string",
  "label": "string",       // tab label
  "icon": "string|null",   // icon hint (e.g. lucide name)
  "description": "string|null",
  "layout": "string|null", // e.g. "stack", "grid-2col", "grid-3col"
  "blocks": [...]          // inline block definitions
}
```

Key change: `block_ids` reference → inline `blocks` array. This makes each view self-contained and allows LLM to generate the complete structure in one pass.

### 4.4 Full Spec Schema

```jsonc
{
  "version": "tilo/aip/v1",
  "title": "string",
  "views": [ /* View[] */ ],
  "confirmations": [ /* Confirmation[] */ ],
  "memory_candidates": [ /* MemoryCandidate[] */ ],
  "follow_ups": [ "string" ],
  "provenance": {
    "agent_id": "string",
    "run_id": "string",
    "skill_id": "string|null"
  }
}
```

Note: `artifact_type` is **removed**. The spec is type-agnostic — the combination of views and blocks implicitly defines what it is. This eliminates the need for type-detection logic.

---

## 5. Protocol Adapters (Layer 2)

### 5.1 MCP Adapter

```python
from tilo.adapters.mcp import mcp_to_blocks

# MCP tool result → Tilo blocks
blocks = mcp_to_blocks(mcp_result.content)
# TextContent   → markdown block
# ImageContent  → image block
# Resource      → card block with embedded preview
```

### 5.2 LangChain Adapter

```python
from tilo.adapters.langchain import TiloCallbackHandler

# Drop-in callback — captures LC output as Tilo spec
chain.invoke(input, config={"callbacks": [TiloCallbackHandler(run_id=run_id)]})
# AIMessage          → markdown block
# ToolMessage        → tool_preview block
# Structured output  → mapped to matching block types
```

### 5.3 A2A / ACP Adapters

```python
from tilo.adapters.a2a import a2a_task_to_spec
from tilo.adapters.acp import acp_message_to_spec
```

### 5.4 Adapter Priority

1. **MCP** — de facto standard, cleanest mapping
2. **A2A** — growing adoption, Google-backed
3. **ACP** — important for Chinese ecosystem
4. **LangChain/LangGraph** — largest user base, callback-based

---

## 6. Renderer SDK (Layer 3)

### 6.1 Design Principle

The SDK is a **block-type → component** dispatch table. Nothing more.

```typescript
// @tilo/react — core concept
interface TiloRendererProps {
  spec: TiloSpec;
  overrides?: Record<string, React.ComponentType<BlockProps>>;
}

function TiloRenderer({ spec, overrides }: TiloRendererProps) {
  const renderers = { ...DEFAULT_RENDERERS, ...overrides };
  return (
    <TiloTabs views={spec.views}>
      {(view) =>
        view.blocks.map(block => {
          const Component = renderers[block.type] ?? GenericBlock;
          return <Component key={block.id} {...block.props} actions={block.actions} />;
        })
      }
    </TiloTabs>
  );
}
```

### 6.2 Multi-framework Strategy

| Package | Framework | Status |
|---------|-----------|--------|
| `@tilo/react` | React / Next.js | Official, reference implementation |
| `@tilo/vue` | Vue 3 | Community contribution welcome |
| `@tilo/web-components` | Framework-agnostic | Future, maximum portability |
| `@tilo/flutter` | Flutter / Dart | Community contribution welcome |

### 6.3 Renderer Override Pattern

Developers can replace any block type's renderer:

```typescript
import { TiloRenderer } from '@tilo/react';
import MyCustomChart from './MyCustomChart';

<TiloRenderer
  spec={artifactSpec}
  overrides={{
    chart: MyCustomChart,        // replace default chart renderer
    medical_report: MedicalView, // handle a custom block type
  }}
/>
```

Unknown types without overrides → `GenericBlock` (JSON viewer with type badge).

---

## 7. Skill Hints + LLM Composition (Layer 4)

### 7.1 How It Works

Skills do NOT define rigid block structures. They provide **hints** to the LLM:

```yaml
# skills/contract-review/skill.yaml
name: contract-review
version: 1.0.0

block_hints:
  - type: chart
    variant: radar
    use_when: "Showing risk distribution across categories"
  - type: diff
    use_when: "Suggesting contract revisions"
  - type: list
    variant: selectable
    use_when: "Listing contract clauses for review"

view_hints: |
  For contract review, consider organizing into:
  - A "Risk Overview" view with chart + list blocks
  - A "Clauses" view for detailed reading
  - A "Revisions" view with diff blocks
  Adapt based on what the user actually asked for.
```

### 7.2 LLM Prompt Integration

```
You are generating a Tilo AIP spec. Available block types:
{core_primitive_types}

The active skill provides these hints:
{skill.block_hints}
{skill.view_hints}

Generate a complete spec with views and blocks based on the user's goal.
You may use any core block type. You may also use custom types if no
core type fits — the frontend will render them with a generic fallback.
```

### 7.3 Key Principle

The LLM has **full autonomy** over:
- Which views to create
- Which blocks to include
- Block ordering and layout
- View labels and icons
- Whether to follow skill hints or deviate

Skills are recommendations, not constraints.

---

## 8. Tilo-unique Value (Why Not Just JSON?)

What makes Tilo AIP more than "just a JSON schema for UI":

| Capability | Description |
|------------|-------------|
| **Confirmation** | Actions can require human approval before execution. Durable confirmation records, not ephemeral button clicks. |
| **Memory** | Agent output can include memory candidates. Confirmed memories persist across sessions and are recallable in future runs. |
| **Trace** | Every step from goal → spec generation → rendering is traceable. |
| **Follow-ups** | LLM generates contextual next questions, enabling multi-turn workflows. |
| **State Binding** | Blocks can bind to runtime state (run status, confirmation status), enabling live updates. |
| **Action Semantics** | Backend owns action meaning. Frontend only renders intent. Decoupled and safe. |

This is what separates Tilo from "render a JSON as UI" libraries.

---

## 9. Migration from v0.x

### What changes

| Area | v0.x | AIP v1 |
|------|------|--------|
| Block type set | 26 pre-defined (closed) | ~20 primitives (stable) + open extension |
| Block data field | `data: dict` | `props: dict` (naming convention) |
| Views | `block_ids` reference | Inline `blocks` array |
| artifact_type | Required, drives spec builder | Removed — views/blocks define shape |
| spec.py | 924-line hardcoded builder | LLM-generated with skill hints |
| Domain blocks | In framework core | Moved to skill packages |
| Frontend renderers | Hardcoded registry | Dispatch table with override support |
| Ecosystem integration | None | Adapters for MCP/ACP/A2A/LangChain |

### What stays the same

- Memory engine (recall, candidates, confirmation)
- Confirmation inbox
- Trace recorder
- ROAM loop (Render → Observe → Act → Memorize)
- FastAPI + SQLAlchemy backend
- Next.js reference frontend

---

## 10. Open Questions

1. **Block type namespace** — Should custom types use a prefix (e.g. `x-medical-report`) to avoid collision with future core types?
2. **Renderer distribution** — How should skill-provided renderers be distributed? npm packages? CDN URLs? Bundled in skill YAML?
3. **Spec validation** — Should the backend validate block props against a schema, or treat props as opaque? (Recommendation: opaque for flexibility, with optional validation via skill-provided schemas.)
4. **Streaming** — Should the spec support incremental block updates for long-running tasks?
5. **Versioning** — How to handle spec version migration when primitives evolve?

---

## 11. References

- [MCP Specification](https://modelcontextprotocol.io)
- [A2A Protocol](https://github.com/google/a2a)
- [ACP Protocol](https://github.com/anthropics/acp)
- [HTML Living Standard — Elements](https://html.spec.whatwg.org/multipage/semantics.html)
- [Tilo ROAM Loop](./ROAM_LOOP.md)
- [Tilo AI-native Principles](./AI_NATIVE_FRAMEWORK_PRINCIPLES.md)
