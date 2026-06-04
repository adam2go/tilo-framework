# Tilo Framework

<p align="center">
  <strong>The open-source runtime for AI-native software — agents author the UI, every user action returns as structured signal.</strong>
</p>

<p align="center">
  <a href="./README.zh-CN.md">中文</a> ·
  <a href="./docs/AIP_DESIGN.md">AIP Design</a> ·
  <a href="./docs/INTEGRATION_GUIDE.md">Integration</a> ·
  <a href="./docs/BUILD_YOUR_FIRST_TILO_APP.md">Build an App</a> ·
  <a href="./docs/MEMORY.md">Memory</a> ·
  <a href="./docs/README.md">Docs</a>
</p>

<p align="center">
  <img alt="License" src="https://img.shields.io/github/license/adam2go/tilo-framework" />
  <img alt="Stars" src="https://img.shields.io/github/stars/adam2go/tilo-framework?style=social" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-blue" />
  <img alt="pip install" src="https://img.shields.io/badge/pip%20install-tilo-indigo" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-backend-009688" />
  <img alt="Next.js" src="https://img.shields.io/badge/Next.js-reference_UI-black" />
</p>

---

## See it in 60 seconds

A real Tilo run — agent recalls memory, plans, calls tools, generates an
interactive artifact, and hands it back to the user as live, clickable UI.
**Zero LLM key required for this demo.**

https://github.com/user-attachments/assets/1afed79d-e85e-414a-954f-e0be136b9c7d

> **Plan a SF weekend** — runs entirely from a baked-in fixture. Two more
> demos (PR Review · Sales Briefing) further down. ↓

<p align="center">
  <img alt="Tilo AIP: Agent Interaction Protocol — four-layer architecture" src="./docs/assets/tilo-framework-overview.svg" />
</p>

---

## Why Tilo

The AI agent ecosystem has good answers for **tool calling** (MCP),
**orchestration** (LangChain, CrewAI), and **agent-to-agent communication**
(A2A, ACP).

What's still missing is the **runtime for AI-native software** — software
where the agent doesn't drive a UI built for humans, but **authors the UI
itself**, and every user action flows back to the agent as structured
signal.

```
MCP   = Agent's hands         (call tools)
A2A   = Agent's voice          (talk to other agents)
Tilo  = Agent's face + ears    (render UI, observe what users do with it)
```

Tilo is an **Agent Interaction Protocol (AIP)**: a declarative JSON spec
that closes the loop between agent and user. The agent emits a spec; the
runtime renders it as interactive UI; every click, edit, or confirmation
is captured as a typed `UIInteractionEvent` and fed into the agent's next
turn — without DOM scraping or pixel inspection.

### Tilo and Browser Use solve different problems

|                            | **Browser Use**                                  | **Tilo**                                              |
|----------------------------|--------------------------------------------------|-------------------------------------------------------|
| Software it powers         | Existing apps designed for humans                | New apps where the agent generates the UI             |
| Agent's relationship to UI | Drives a UI it didn't author                     | Authors the UI from a spec on every turn              |
| User → agent feedback      | Inferred from screenshots and DOM                | Captured as structured `UIInteractionEvent`           |
| Where it fits              | Automating workflows on existing software        | Building AI-native products from the ground up        |

If you need to automate an existing app, Browser Use is the right tool.
Tilo is for the case where you can choose what the UI looks like, and
you want it shaped for both humans and agents from day one.

---

## 30-second Quick Start

```bash
pip install tilo
tilo serve
```

Open `http://localhost:8000/api/health` to confirm the backend is running.

For the full experience with the reference frontend:

```bash
git clone https://github.com/adam2go/tilo-framework.git
cd tilo-framework
make install   # pip install + pnpm install
make dev       # backend :8000 + frontend :4001 (Ctrl-C stops both)
```

Two entry points:

- `http://localhost:4001/demo` — classic scenario picker
- `http://localhost:4001/canvas` — **3D Agent Canvas**: watch the agent stream a live trace and render an interactive spatial workspace

> **Zero-config demo.** The canvas works without any LLM key — the "Plan a SF Weekend" sample runs from a baked-in fixture. Configure `LLM_ENABLED=true` + a provider key in `.env` to unlock the LLM-driven samples.

---

## Architecture: Four Layers

### Layer 1 — Core Spec + Runtime

~20 **primitive block types** (like HTML tags: `markdown`, `table`, `chart`, `diff`, `form`, `card`, …) plus an open extension mechanism. Any string is a valid block type — unknown types render with a generic JSON fallback.

Three runtime pillars: **Memory Engine** (recall → candidate → confirm), **Confirmation Inbox** (gate high-risk actions), **Trace Recorder** (every step auditable).

### Layer 2 — Protocol Adapters

Zero-code bridges from external protocols into Tilo blocks:

| Adapter | Status | Mapping |
|---|---|---|
| **MCP** | ✅ Implemented | TextContent→markdown, ImageContent→image, Resource→card |
| **LangChain** | ✅ Implemented | `TiloCallbackHandler` captures LLM text, tool calls, and structured output as typed blocks |
| **A2A** | 🔌 Interface | A2A task result → Tilo spec |
| **ACP** | 🔌 Interface | ACP message → Tilo spec |

### Layer 3 — Renderer SDKs

Tilo Spec JSON → any frontend. `@adam2go/tilo-react` is the official reference. Developers can override any block type's renderer or build their own SDK for Vue, Flutter, Web Components, or terminal CLI.

### Layer 4 — Skill Hints + LLM Composition

Skills provide **hints** (recommended block types, view organization) to the LLM. The LLM has full autonomy to decide the final views, blocks, and layout. Skills are recommendations, not constraints.

---

## Three Built-in Demos

| Scenario | What the agent does | Mode |
|---|---|---|
| **PR Review** 🔍 | Flags risky changes in a pull request, lists verification items, gates the merge with a confirmation | LLM |
| **SF Trip** ✈️ | Plans a 3-day weekend with timeline, hotels, packing checklist, budget — fully interactive | offline · zero-config |
| **Sales Briefing** 📊 | Surfaces pipeline metrics + recommended actions + a ready-to-send email behind a confirmation | LLM |

The SF Trip video is at the top of this page. The other two:

<table>
  <tr>
    <td width="50%" valign="top">
      <h4>🔍 PR Review</h4>

https://github.com/user-attachments/assets/3795a3a8-aedb-4996-ae18-42f7c3e2c45f

  <sub>Auth-refactor PR · diffs + verification checklist + merge confirmation. <b>53s</b> · <a href="https://github.com/adam2go/tilo-framework/releases/download/v0.1-demos/canvas-pr-review.mp4">HQ download (42 MB)</a></sub>
    </td>
    <td width="50%" valign="top">
      <h4>📊 Sales Briefing</h4>

https://github.com/user-attachments/assets/1847718a-586d-4e80-b9fd-6eade1d35b35

  <sub>Pipeline metrics + recommended actions + gated outbound email. <b>68s</b> · <a href="https://github.com/adam2go/tilo-framework/releases/download/v0.1-demos/canvas-sales-briefing.mp4">HQ download (36 MB)</a></sub>
    </td>
  </tr>
</table>

See [`docs/demos/`](./docs/demos/README.md) for the full goal text and reproduction steps.

[demos-release]: https://github.com/adam2go/tilo-framework/releases/tag/v0.1-demos

---

## The Two-Way Loop, Concretely

Most "agent UI" frameworks ship one direction: agent → UI. Tilo ships
both directions, and the second one is where the leverage is.

```text
1.  Agent emits AIP spec        →  blocks + views, declarative JSON
2.  Renderer paints UI          →  React (reference) / your own SDK
3.  User clicks / edits / confirms
4.  Frontend → POST /api/interactions
5.  Backend writes UIInteractionEvent + ContextReflection observation
6.  Next agent turn picks up recent events via AgentContextBuilder
7.  Agent reasons over what the user actually did, not pixels.
```

Two design choices keep this safe:

- **Confirmed memory, not automatic memory.** The agent proposes what it
  learned (`memory_card`); the user decides what sticks.
- **Backend-owned action semantics.** The frontend renders intent; the
  backend (via `ArtifactActionRuntime`) decides what actually happens —
  so high-risk actions stay gated behind a `confirmation` block.

---

## How Developers Integrate

| Mode | When to use | What you touch |
|---|---|---|
| **Standalone** | Evaluate Tilo locally | `pip install tilo && tilo serve` |
| **MCP adapter** | Already using MCP tools | `from tilo.adapters.mcp import mcp_content_to_blocks` |
| **LangChain adapter** | Using LangChain / LangGraph | `from tilo.adapters.langchain import TiloCallbackHandler` |
| **Backend sidecar** | Have your own frontend | Call Tilo REST APIs |
| **Embedded components** | Want AI-native UI blocks | Reuse `@adam2go/tilo-react` components with overrides |
| **Skill author** | Package a repeatable workflow | `skill.yaml` with `block_hints` + `view_hints` |
| **Declarative app** | Full agent workflow | `app.yaml` + `interaction.policy.yaml` |

Core APIs:

```text
POST /api/conversations                          Create a session
POST /api/conversations/{id}/messages             Send a message → Task → Run
GET  /api/runs/{id}/trace                         Live trace stream
GET  /api/artifacts?workspace_id=...&task_id=...  Full artifact with views
POST /api/memories/{id}/confirm                   Confirm a memory candidate
```

See [`docs/INTEGRATION_GUIDE.md`](./docs/INTEGRATION_GUIDE.md) and [`docs/AIP_DESIGN.md`](./docs/AIP_DESIGN.md).

---

## Repository Structure

```text
backend/       Python package `tilo` — FastAPI runtime, pip-installable
  tilo/adapters/   MCP, LangChain, A2A, ACP protocol adapters
  tilo/schemas/    AIP v1 spec: ~20 primitive block types + open extension
  tilo/services/   Memory, Confirmation, Trace, Artifact, Skills
frontend/      @adam2go/tilo-react — Next.js reference UI, artifact-driven Canvas
skills/        Skill YAML definitions with block_hints + view_hints
examples/      Declarative agent apps and contract fixtures
docs/          Architecture, AIP design, integration guide, principles
evals/         Runtime quality checks and baseline metrics
```

---

## Roadmap

**v0.1 (current)** — Complete working loop + AIP architecture.

- [x] Task → Run → Trace → Artifact → Surface → Confirmation → Memory loop
- [x] Three demo scenarios (PR Review, SF Trip, Sales Briefing)
- [x] Agent Interaction Protocol (AIP) with ~20 primitive block types
- [x] LLM-driven UI composition with skill hints
- [x] MCP adapter — `mcp_content_to_blocks`, `mcp_tool_result_to_spec`
- [x] LangChain adapter — `TiloCallbackHandler` + `langchain_result_to_spec`
- [x] Three declarative example apps (contract-review, sales-followup, code-review)
- [x] Alembic-managed schema migrations
- [x] `pip install tilo` + `tilo serve` CLI
- [x] Multi-turn conversation + LLM streaming with visible thinking
- [x] Chart, diff, timeline, kanban, code, tool_preview, memory_card block rendering
- [x] PyPI publication — `pip install tilo` is live
- [ ] A2A / ACP adapter implementations
- [ ] `@adam2go/tilo-react` npm package published to npm
- [ ] Skill marketplace + YAML-based skill loading

**Future** — Multi-agent routing, real tool execution with confirmation gates, Slack / email channel adapters, community renderer SDKs.

---

## Contributing

Tilo is early-stage and open source. Contributions are welcome.

Before contributing, please read:

- [`AGENTS.md`](./AGENTS.md) — Development rules for AI coding agents
- [`CONTRIBUTING.md`](./CONTRIBUTING.md)
- [`docs/AIP_DESIGN.md`](./docs/AIP_DESIGN.md) — Agent Interaction Protocol design

The most important principle:

> **MCP is the Agent's hands. Tilo is the Agent's face and ears.
> Preserve the AIP loop: Goal → Spec → Interactive UI → Observation → Memory.**

---

## License

MIT License
