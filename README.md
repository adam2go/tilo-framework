# Tilo Framework

<p align="center">
  <strong>Agent Interaction Protocol — the open-source runtime that turns Agent output into interactive, confirmable, memorable UI.</strong>
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

<!--
  ▼ HERO VIDEO ▼
  Replace this URL with the GitHub user-attachments link once uploaded:
    1. Open https://github.com/adam2go/tilo-framework/issues/new
    2. Drag examples/compressed/canvas-sf-trip.mp4 into the description
    3. Copy the auto-generated user-attachments URL into the src below
-->

https://github.com/adam2go/tilo-framework/releases/download/v0.1-demos/canvas-sf-trip.mp4

> **Plan a SF weekend** — runs entirely from a baked-in fixture. Two more
> demos (PR Review · Sales Briefing) further down. ↓

<p align="center">
  <img alt="Tilo AIP: Agent Interaction Protocol — four-layer architecture" src="./docs/assets/tilo-framework-overview.svg" />
</p>

---

## Why Tilo

The AI agent ecosystem already has great solutions for **tool calling** (MCP), **agent orchestration** (LangChain, CrewAI), and **agent communication** (A2A, ACP).

What's missing? **The last mile between Agent output and user screen.**

```
MCP  = Agent's hands  (how agents call tools)
A2A  = Agent's voice   (how agents talk to each other)
Tilo = Agent's face    (how agent output becomes interactive UI)
```

Tilo is an **Agent Interaction Protocol (AIP)**: a declarative JSON spec that turns agent output into interactive surfaces with built-in support for confirmation, memory, and traceability — across any frontend framework.

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

- `http://localhost:4001/demo` — classic scenario picker (Contract Review, Sales, Competitive)
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
| **LangChain** | 🔌 Interface | TiloCallbackHandler → Tilo spec |
| **A2A** | 🔌 Interface | A2A task result → Tilo spec |
| **ACP** | 🔌 Interface | ACP message → Tilo spec |

### Layer 3 — Renderer SDKs

Tilo Spec JSON → any frontend. `@tilo/react` is the official reference. Developers can override any block type's renderer or build their own SDK for Vue, Flutter, Web Components, or terminal CLI.

### Layer 4 — Skill Hints + LLM Composition

Skills provide **hints** (recommended block types, view organization) to the LLM. The LLM has full autonomy to decide the final views, blocks, and layout. Skills are recommendations, not constraints.

---

## Three Built-in Demos

Each demo exercises the same runtime. The Canvas adapts automatically based on what the agent produces.

| Scenario | What the agent does | Mode |
|---|---|---|
| **PR Review** 🔍 | Flags risky changes in a pull request, lists verification items, gates the merge with a confirmation | LLM |
| **SF Trip** ✈️ | Plans a 3-day weekend with timeline, hotels, packing checklist, budget — fully interactive | offline · zero-config |
| **Sales Briefing** 📊 | Surfaces pipeline metrics + recommended actions + a ready-to-send email behind a confirmation | LLM |

All three support **multi-turn conversation** and **LLM-driven UI composition** — the LLM decides which block types and views to generate based on skill hints and user intent.

### 📹 The other two demos

> The SF Trip demo is at the top of this page. Below are the two LLM-driven scenarios:

<table>
  <tr>
    <td width="50%" valign="top">
      <h4>🔍 PR Review</h4>
      <video src="https://github.com/adam2go/tilo-framework/releases/download/v0.1-demos/canvas-pr-review.mp4" controls width="100%"></video>
      <sub>Auth-refactor PR · diffs + verification checklist + merge confirmation. <b>53s</b></sub><br/>
      <a href="https://github.com/adam2go/tilo-framework/releases/download/v0.1-demos/canvas-pr-review.mp4">▶ Watch (42 MB)</a>
    </td>
    <td width="50%" valign="top">
      <h4>📊 Sales Briefing</h4>
      <video src="https://github.com/adam2go/tilo-framework/releases/download/v0.1-demos/canvas-sales-briefing.mp4" controls width="100%"></video>
      <sub>Pipeline metrics + recommended actions + gated outbound email. <b>68s</b></sub><br/>
      <a href="https://github.com/adam2go/tilo-framework/releases/download/v0.1-demos/canvas-sales-briefing.mp4">▶ Watch (36 MB)</a>
    </td>
  </tr>
</table>

See [`docs/demos/`](./docs/demos/README.md) for the full goal text, expected blocks, and how to reproduce each demo locally.

[demos-release]: https://github.com/adam2go/tilo-framework/releases/tag/v0.1-demos

---

## What Makes Tilo Different

### 1. Open Block Type System

Unlike fixed component libraries, Tilo's ~20 primitives are **stable and extensible**. Use core types for 95% of cases. Define custom types for domain-specific needs — the frontend degrades gracefully with a generic JSON viewer.

### 2. Confirmed Memory — Not Automatic Memory

```text
Observation → Memory Candidate → Human Confirmation → Confirmed Memory
```

The agent proposes what it learned. The user decides what sticks.

### 3. Backend-Owned Action Semantics

```text
User click → ArtifactActionRuntime → UIInteractionEvent → Observation → Safe side effect
```

The frontend renders intent. The backend owns what happens.

### 4. Protocol-Native Integration

Bring your own agent framework. Tilo adapters bridge MCP tool results, LangChain outputs, A2A tasks, and ACP messages into the same interactive Canvas — without rewriting your agent logic.

---

## How Developers Integrate

| Mode | When to use | What you touch |
|---|---|---|
| **Standalone** | Evaluate Tilo locally | `pip install tilo && tilo serve` |
| **MCP adapter** | Already using MCP tools | `from tilo.adapters.mcp import mcp_content_to_blocks` |
| **Backend sidecar** | Have your own frontend | Call Tilo REST APIs |
| **Embedded components** | Want AI-native UI blocks | Reuse `@tilo/react` components with overrides |
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
frontend/      @tilo/react — Next.js reference UI, artifact-driven Canvas
skills/        Skill YAML definitions with block_hints + view_hints
examples/      Declarative agent apps and contract fixtures
docs/          Architecture, AIP design, integration guide, principles
evals/         Runtime quality checks and baseline metrics
```

---

## Roadmap

**v0.1 (current)** — Complete working loop + AIP architecture.

- [x] Task → Run → Trace → Artifact → Surface → Confirmation → Memory loop
- [x] Three demo scenarios (contract, sales, competitive)
- [x] Agent Interaction Protocol (AIP) with ~20 primitive block types
- [x] LLM-driven UI composition with skill hints
- [x] MCP adapter (implemented) + LangChain/A2A/ACP stubs
- [x] `pip install tilo` + `tilo serve` CLI
- [x] Multi-turn conversation + LLM streaming with visible thinking
- [ ] Full adapter implementations (LangChain, A2A, ACP)
- [ ] `@tilo/react` npm package with renderer override API
- [ ] Skill marketplace + YAML-based skill loading
- [ ] PyPI publication

**Future** — Multi-agent routing, real tool execution with confirmation gates, community renderer SDKs.

---

## Contributing

Tilo is early-stage and open source. Contributions are welcome.

Before contributing, please read:

- [`AGENTS.md`](./AGENTS.md) — Development rules for AI coding agents
- [`CONTRIBUTING.md`](./CONTRIBUTING.md)
- [`docs/AIP_DESIGN.md`](./docs/AIP_DESIGN.md) — Agent Interaction Protocol design

The most important principle:

> **MCP is the Agent's hands. Tilo is the Agent's face. Preserve the AIP loop: Goal → Spec → Interactive UI → Decision → Memory.**

---

## License

MIT License
