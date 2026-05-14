# Tilo Framework

<p align="center">
  <strong>The open-source runtime for AI agents that render decisions, execute actions, and build confirmed memory.</strong>
</p>

<p align="center">
  <a href="./README.zh-CN.md">中文</a> ·
  <a href="./docs/INTEGRATION_GUIDE.md">Integration</a> ·
  <a href="./docs/BUILD_YOUR_FIRST_TILO_APP.md">Build an App</a> ·
  <a href="./docs/ARTIFACT_ACTION_RUNTIME.md">Action Runtime</a> ·
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
  <img alt="Dependencies" src="https://img.shields.io/badge/runtime_deps-8-green" />
</p>

---

## Why Tilo

Most AI agent frameworks stop at **orchestrating LLM calls**. They give you chains, graphs, and tool routers — but leave you to figure out how to actually ship that as a product.

Tilo picks up where they leave off. It is the **product runtime layer** between your agent's reasoning and your user's screen:

```text
Goal → Surface → Decision → Action → Memory
```

An agent powered by Tilo doesn't just return text. It **renders a focused UI**, asks the human for a **real decision**, executes the action through **backend-owned semantics**, and only commits to memory what the human **explicitly confirms**.

This is the difference between an AI demo and an AI-native product.

---

## 30-second Quick Start

```bash
pip install tilo
tilo serve
```

That's it. Open `http://localhost:8000/api/health` to confirm the backend is running.

For the full experience with the reference frontend:

```bash
git clone https://github.com/adam2go/tilo-framework.git
cd tilo-framework
make install   # pip install + pnpm install
make dev       # backend :8000 + frontend :3000
```

Open `http://localhost:3000/demo` — pick a scenario and watch the agent think, render, and ask for your decision.

---

## Three Built-in Demos

Each demo exercises the same underlying runtime. The Canvas adapts automatically based on what the agent produces — no frontend changes needed.

| Scenario | What the agent does | Canvas views |
|---|---|---|
| **Contract Review** 📋 | Reads a full contract, flags 8 risks by clause, drafts conservative revisions | Risks · Clauses · Revision · Memory |
| **Sales Follow-up** 📊 | Analyzes pipeline, ranks hot accounts, suggests outbound actions | Pipeline · Next Actions |
| **Competitive Analysis** 🏆 | Compares market positioning, identifies gaps and strengths | Comparison · Next Steps |

All three support **multi-turn conversation**: after the first run completes, context-aware follow-up suggestions appear based on what the agent actually produced.

---

## What Makes Tilo Different

### 1. Confirmed Memory — Not Automatic Memory

Many agents silently write to memory. This pollutes evaluations, stores wrong preferences, and erodes user trust.

Tilo treats memory as a lifecycle with human gates:

```text
Observation → Memory Candidate → Human Confirmation → Confirmed Memory
```

The agent proposes what it learned. The user decides what sticks.

### 2. Backend-Owned Action Semantics

In typical AI demos, a frontend button calls an API and mutates state directly. This breaks auditability and forces every channel to reimplement logic.

Tilo routes every meaningful action through the Artifact Action Runtime:

```text
User click → ArtifactActionRuntime → UIInteractionEvent → Observation → Safe side effect
```

The frontend renders intent. The backend owns what happens.

### 3. Artifact-Driven Canvas — Not Hardcoded UIs

The right-hand Canvas is not a fixed dashboard. It reads `views` declared by each artifact and renders the matching block types. A contract review agent produces Risks/Clauses/Revision tabs. A sales agent produces Pipeline/Actions tabs. **The Canvas never changes — only the artifact does.**

Any new agent can declare its own views and block types. The frontend stays unchanged.

### 4. Lightweight by Design

```text
Backend:   8 runtime dependencies · 103 source files · pip install tilo
Frontend:  4 runtime dependencies · 32 source files  · pnpm install
```

No LangChain. No vector database required. No heavyweight orchestration layer. SQLite works out of the box. Postgres when you're ready.

---

## Protocol Boundary

MCP connects tools. AG-UI streams agent/UI events. LangGraph orchestrates graphs. A2A routes between agents.

Tilo doesn't compete with any of them — it sits one layer above. It owns the **product runtime loop**: the part where an agent's output becomes a human-facing decision, a backend action, and a confirmed memory. MCP, AG-UI, ACP, or A2A can all serve as boundary adapters underneath.

---

## How Developers Integrate

Tilo is designed for gradual adoption. You don't rewrite your product.

| Mode | When to use | What you touch |
|---|---|---|
| **Standalone** | Evaluate Tilo locally | `pip install tilo && tilo serve` |
| **Backend sidecar** | You already have a frontend | Call Tilo REST APIs |
| **Embedded components** | Want AI-native UI building blocks | Reuse React artifact/action components |
| **Declarative app** | Package a repeatable agent workflow | `app.yaml` + `interaction.policy.yaml` |

Core APIs:

```text
POST /api/conversations                          Create a session
POST /api/conversations/{id}/messages             Send a message → Task → Run
GET  /api/runs/{id}/trace                         Live trace stream
GET  /api/runs/{id}/surface-turns                 Rendered surfaces
GET  /api/artifacts?workspace_id=...&task_id=...  Full artifact with views
POST /api/memories/{id}/confirm                   Confirm a memory candidate
```

See [`docs/INTEGRATION_GUIDE.md`](./docs/INTEGRATION_GUIDE.md) for the full guide.

---

## Build an Agent App

A Tilo app is a small declarative folder:

```text
my-agent/
  app.yaml                    # Agent identity and capabilities
  interaction.policy.yaml     # When to show UI vs. stay silent
  fixtures/                   # Sample inputs (optional)
  README.md
```

Scaffold one:

```bash
tilo init my-agent           # or: python scripts/create_app.py my-agent
```

Three built-in examples:

```text
examples/apps/contract-review-agent/
examples/apps/sales-followup-agent/
examples/apps/competitive-analysis-agent/
```

References: [`BUILD_YOUR_FIRST_TILO_APP.md`](./docs/BUILD_YOUR_FIRST_TILO_APP.md) · [`APP_MANIFEST.md`](./docs/APP_MANIFEST.md) · [`INTERACTION_POLICY.md`](./docs/INTERACTION_POLICY.md)

---

## Runtime Model

```text
User Goal
  → Task + Run
    → Memory Recall
    → Skill Selection
    → Tool Execution
    → LLM Generation (streaming thinking visible in trace)
    → Interaction Policy (per-step: surface / silent / collect input)
    → Artifact + Views (Canvas tabs auto-generated)
    → Surface Turns (chat-side decisions)
    → Confirmation Inbox (high-risk actions gated)
    → Memory Candidates (human-confirmed only)
```

Every step is recorded in the Trace. Every action creates a UIInteractionEvent. Every memory requires confirmation. Nothing is hidden.

---

## Repository Structure

```text
backend/       Python package `tilo` — FastAPI runtime, 8 deps, pip-installable
frontend/      @tilo/frontend — Next.js reference UI, 4 deps, artifact-driven Canvas
examples/      Declarative agent apps and contract fixtures
docs/          Architecture, protocols, integration guide, principles
evals/         Runtime quality checks and baseline metrics
scripts/       App scaffold, validation, local verification
```

---

## Roadmap

**v0.1 (current)** — Complete working loop with three end-to-end demos.

- [x] Backend + frontend run locally
- [x] Task → Run → Trace → Artifact → Surface → Confirmation → Memory loop
- [x] Three demo scenarios (contract, sales, competitive)
- [x] Multi-turn conversation with context-aware follow-ups
- [x] Artifact-driven Canvas with dynamic views
- [x] `pip install tilo` + `tilo serve` CLI
- [x] LLM streaming with visible thinking in trace
- [ ] CI pipeline with green verification
- [ ] PyPI publication
- [ ] npm package for frontend components

**Future** — Skill marketplace, MCP adapter layer, multi-agent routing, real tool execution with confirmation gates.

---

## Contributing

Tilo is early-stage and open source. Contributions are welcome.

Before contributing, please read:

- [`AGENTS.md`](./AGENTS.md) — Development rules for AI coding agents
- [`CONTRIBUTING.md`](./CONTRIBUTING.md)
- [`docs/PROJECT_CONSTITUTION.md`](./docs/PROJECT_CONSTITUTION.md)

The most important rule:

> **Do not turn Tilo into "SaaS + AI sidebar". Preserve the AI-native runtime loop: Goal → Surface → Decision → Action → Memory.**

---

## License

MIT License
