# Tilo Framework

<p align="center">
  <strong>Build AI-native SaaS agents with the ROAM Loop: Render, Observe, Act, Memorize.</strong>
</p>

<p align="center">
  <a href="./README.zh-CN.md">中文</a> ·
  <a href="./docs/ROAM_LOOP.md">ROAM Loop</a> ·
  <a href="./docs/ROAM_INTERACTION_CONTRACT.md">Interaction Contract</a> ·
  <a href="./docs/INTEROPERABILITY.md">Interoperability</a> ·
  <a href="./docs/AI_NATIVE_INTERACTION_COMPONENTS.md">AI-native Components</a> ·
  <a href="./docs/USER_GUIDE.md">User Guide</a> ·
  <a href="./docs/V0_2_CODEX_PLAN.md">v0.2 Plan</a> ·
  <a href="./evals/README.md">Evals</a>
</p>

<p align="center">
  <img alt="License" src="https://img.shields.io/github/license/adam2go/tilo-framework" />
  <img alt="Stars" src="https://img.shields.io/github/stars/adam2go/tilo-framework?style=social" />
  <img alt="Forks" src="https://img.shields.io/github/forks/adam2go/tilo-framework?style=social" />
  <img alt="Issues" src="https://img.shields.io/github/issues/adam2go/tilo-framework" />
  <img alt="Last Commit" src="https://img.shields.io/github/last-commit/adam2go/tilo-framework" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-blue" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-backend-009688" />
  <img alt="Next.js" src="https://img.shields.io/badge/Next.js-frontend-black" />
</p>

---

## What is Tilo?

**Tilo is an open-source framework for building AI-native SaaS agents that can render interactive product surfaces, observe human interaction, act through tools, and memorize confirmed learning.**

Tilo introduces the **ROAM Loop**:

```text
Render -> Observe -> Act -> Memorize
```

Most agent frameworks focus on reasoning, tool calling, workflow orchestration, or multi-agent coordination. Tilo focuses on a different question:

> What if the user interface itself became part of the agent loop?

In Tilo, an agent does not only produce text or call tools. It can render interactive SaaS-like artifacts, observe how users approve, edit, select, reject, and refine those artifacts, act on those observations, and turn confirmed learning into long-term memory.

Tilo is not a chatbot wrapper. It is an **AI-native SaaS interaction framework**.

---

## The ROAM Loop

Traditional agent loops such as ReAct usually treat observation as tool output or environmental feedback.

Tilo extends this idea:

> Human interaction with generated UI is also observation.

```text
Render
  The agent renders an interactive artifact or component surface.

Observe
  The system captures user actions, edits, approvals, selections, feedback, and tool results as structured observations.

Act
  The agent continues work: update artifacts, invoke tools, create confirmations, ask clarifying questions, or start follow-up tasks.

Memorize
  Confirmed decisions, preferences, project facts, and reusable procedures become inspectable long-term memory.
```

ROAM turns UI from a passive display layer into an active part of the agent runtime.

| Traditional Agent Loop | Tilo ROAM Loop |
|---|---|
| Observation is mostly tool output | Observation includes human UI interaction |
| Output is often text or tool result | Output is an interactive artifact page |
| UI is outside the loop | UI is part of the loop |
| Human-in-the-loop is mostly approval | Human interaction becomes structured observation |
| Memory is optional | Memory closes the loop |

Read more: [`docs/ROAM_LOOP.md`](./docs/ROAM_LOOP.md)

---

## Why Tilo?

Traditional SaaS asks users to operate software:

```text
Open app -> find feature -> fill form -> click buttons -> inspect result -> decide next step
```

Tilo explores AI-native SaaS delivery:

```text
Describe goal -> Agent renders artifact -> User interacts -> Agent acts -> Memory improves next run
```

This means common SaaS components can become agent-generated interaction components:

| Traditional SaaS | Tilo AI-native Replacement |
|---|---|
| Form | Conversational goal + clarification component |
| Table | DecisionTable / ComparisonMatrix |
| Dashboard | MetricDashboard with next actions |
| Modal confirm | Durable Confirmation / ApprovalCard |
| Workflow stepper | Agent Run Progress + ActionQueue |
| Settings page | Memory / Tool / Skill review components |
| Report page | Interactive Artifact page |
| Notification center | Inbox with pending decisions |
| CRUD editor | EditableArtifact with version history |

Read more: [`docs/AI_NATIVE_INTERACTION_COMPONENTS.md`](./docs/AI_NATIVE_INTERACTION_COMPONENTS.md)

---

## ROAM Interaction Contract

Tilo provides a lightweight declarative interaction contract layer for AI-native SaaS agents. A contract describes what the agent should render, what user actions should be observed, which actions need confirmation, and what can become memory.

The contract is practical glue between agents, UI, humans, observations, and memory. It is not positioned as a universal standard or replacement for existing agent protocols.

- Contract design: [`docs/ROAM_INTERACTION_CONTRACT.md`](./docs/ROAM_INTERACTION_CONTRACT.md)
- Concrete example: [`examples/interaction-contracts/contract-review.roam.yaml`](./examples/interaction-contracts/contract-review.roam.yaml)

---

## Interoperability

Tilo is designed to work with the broader agent ecosystem instead of replacing it:

- MCP connects tools and resources.
- A2A-style protocols can connect agents for handoff or collaboration.
- Skills package reusable capabilities.
- LangGraph, LlamaIndex, CrewAI, AutoGen, or custom runtimes can still handle orchestration and retrieval.
- Tilo connects agents, UI, humans, observations, and memory through ROAM.

Read more: [`docs/INTEROPERABILITY.md`](./docs/INTEROPERABILITY.md)

---

## Core Features

### 1. ROAM-native Interaction Layer

Tilo treats interaction components as runtime primitives.

- ApprovalCard
- RiskReviewPanel
- ComparisonMatrix
- MetricDashboard
- MemoryCandidateCard
- ToolCallPreview
- ActionQueue
- EditableDocument placeholder
- Durable UIInteractionEvent model direction

### 2. AI-native Artifact Delivery

Agent outputs should become usable product surfaces, not plain Markdown.

- `artifact_spec.v1`
- Schema-driven rendering
- Renderer registry
- Artifact actions
- State bindings
- Confirmation-aware actions
- Durable artifact pages

### 3. Long-term Memory

Tilo treats memory as a first-class system, not raw chat history.

- Structured memory records
- Memory candidates
- User confirmation before long-term persistence
- Workspace/project scoped recall
- Memory recall events
- Memory write events
- Future-ready embedding and rerank support

### 4. Agent Self-improvement

Tilo introduces safe self-improvement primitives.

- Run metrics
- Feedback records
- Skill candidates
- Human review before skill promotion
- Eval scaffolding
- No unsafe self-modification by default

### 5. Human Decision Inbox

Humans should approve important decisions, not operate every workflow step.

- Durable confirmations
- Approve / reject / edit flows
- High-risk tool gates
- Pending decision queue

### 6. Traceable Runtime

Every run produces visible, safe execution traces.

- Task and Run lifecycle
- Trace steps
- Sanitized trace output
- Failed-run handling
- Tool invocation ledger

---

## Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                    Tilo Console                         │
│ Conversation / Artifact Surface / Context / Inbox       │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│                    ROAM Runtime                         │
│      Render -> Observe -> Act -> Memorize               │
└──────────────┬─────────────┬───────────────┬────────────┘
               │             │               │
┌──────────────▼───┐ ┌───────▼───────┐ ┌────▼─────────────┐
│ Artifact Engine  │ │ Observation   │ │ Agent Runtime    │
│ Spec / Registry  │ │ UI Events     │ │ Planner/Executor │
└──────────────┬───┘ └───────┬───────┘ └────┬─────────────┘
               │             │              │
┌──────────────▼─────────────▼──────────────▼─────────────┐
│ Memory Engine / Skill System / Tool Registry / Inbox    │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│              PostgreSQL + pgvector + Redis              │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Requirements

- Docker and Docker Compose
- Node.js 18+ if running frontend manually
- Python 3.11+ if running backend manually

### Run with Docker Compose

```bash
git clone https://github.com/adam2go/tilo-framework.git
cd tilo-framework
cp .env.example .env

docker compose up --build
```

Backend health check:

```bash
curl http://localhost:8000/api/health
```

Open the console:

```text
http://localhost:3000
```

### Run local evals

```bash
python3 evals/runners/run_memory_recall_eval.py
python3 evals/runners/run_artifact_schema_eval.py
python3 evals/runners/run_runtime_loop_eval.py
```

---

## How to Use the Console

The current UI is an early single-page ROAM console.

1. Open `http://localhost:3000`.
2. Pick one of the demo prompts or type your own task.
3. Click **Send Message**.
4. Tilo creates a Task and Run.
5. The agent renders an Artifact in the center panel.
6. The right panel shows Trace, Memory, Skills, Files, and Inbox.
7. Interact with generated components: approve actions, confirm memory, review suggestions.
8. Those interactions become observations for future runs.
9. Confirmed memories can be recalled next time.

Current demo prompts include:

- Contract review
- Sales follow-up
- Competitive analysis

See [`docs/USER_GUIDE.md`](./docs/USER_GUIDE.md) for a more detailed walkthrough.

---

## Example Use Cases

### Contract Review Agent

```text
Review this contract and flag risky clauses around liability, termination, and payment terms.
```

Tilo should render a contract review surface with risk panels, suggested revisions, approval cards, and memory candidates.

### Sales Follow-up Agent

```text
Which customers should sales follow up with this week?
```

Tilo should render a dashboard and decision table with recommended actions and pending approvals.

### Competitive Analysis Agent

```text
Create a competitive analysis for memory-native AI agent frameworks.
```

Tilo should render a comparison matrix with option picking, evidence cards, and follow-up actions.

---

## Project Status

Tilo is currently in early v0.2/v0.3 design and implementation.

| Area | Status |
|---|---|
| Runtime loop | Working foundation |
| ROAM Loop concept | Documented |
| AI-native interaction components | Designed, implementation needed |
| Artifact spec v1 | Working foundation |
| Renderer registry | Working foundation |
| Memory candidates | Working foundation |
| Recall / write events | Working foundation |
| Human confirmation | Working foundation |
| Tool permission gate | Working foundation |
| Self-improvement primitives | Early foundation |
| Evals | Local scaffolding |
| UI polish | Needs major improvement |

The current UI is functional but not yet impressive enough for a public showcase. The next priority is implementing ROAM-native interaction components.

---

## Roadmap

### v0.3: ROAM Interaction Layer

- Add ROAM to README and product docs
- Add UIInteractionEvent model
- Extend Artifact actions and state bindings
- Build interaction component registry
- Implement ApprovalCard, RiskReviewPanel, ComparisonMatrix, MetricDashboard, MemoryCandidateCard, ToolCallPreview, ActionQueue
- Redesign Console around conversation + generated interaction surface
- Make component actions write durable backend state

### v0.4: Memory and Self-improvement

- Hybrid semantic memory recall
- Memory conflict resolver
- Skill candidate review and promotion
- Feedback-driven improvement loop
- Stronger eval benchmarks

### v0.5+

- MCP integration
- Browser and GUI automation
- Artifact sharing and publishing
- Message gateways: Telegram, Slack, Discord, WeChat-style adapters
- Multi-user workspace permissions
- Skill marketplace primitives

---

## Star History

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=adam2go/tilo-framework&type=Date&theme=dark" />
  <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=adam2go/tilo-framework&type=Date" />
  <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=adam2go/tilo-framework&type=Date" />
</picture>

---

## Repository Map

```text
backend/       FastAPI backend, domain models, runtime services, memory, tools, artifacts
frontend/      Next.js console, artifact renderer, memory/trace/inbox panels
docs/          Product principles, ROAM Loop, architecture, user guide, implementation plans
evals/         Local benchmark scaffolding for memory, artifact, and runtime loop
```

---

## Documentation

- [`docs/ROAM_LOOP.md`](./docs/ROAM_LOOP.md) — Tilo's core interaction loop
- [`docs/AI_NATIVE_INTERACTION_COMPONENTS.md`](./docs/AI_NATIVE_INTERACTION_COMPONENTS.md) — AI-native SaaS component system
- [`docs/ROAM_CODEX_IMPLEMENTATION_PLAN.md`](./docs/ROAM_CODEX_IMPLEMENTATION_PLAN.md) — Codex execution plan for ROAM
- [`docs/PROJECT_CONSTITUTION.md`](./docs/PROJECT_CONSTITUTION.md) — project constitution
- [`docs/PRODUCT_PRINCIPLES.md`](./docs/PRODUCT_PRINCIPLES.md) — product philosophy
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — system architecture
- [`docs/MEMORY.md`](./docs/MEMORY.md) — memory system design
- [`docs/ARTIFACTS.md`](./docs/ARTIFACTS.md) — artifact protocol
- [`docs/SKILLS.md`](./docs/SKILLS.md) — skill system
- [`docs/API_CONTRACTS.md`](./docs/API_CONTRACTS.md) — API contracts
- [`docs/USER_GUIDE.md`](./docs/USER_GUIDE.md) — user guide

---

## Contributing

Tilo is still early, but contributions are welcome.

Before contributing, please read:

- [`AGENTS.md`](./AGENTS.md)
- [`CONTRIBUTING.md`](./CONTRIBUTING.md)
- [`docs/PROJECT_CONSTITUTION.md`](./docs/PROJECT_CONSTITUTION.md)
- [`docs/QUALITY_BAR.md`](./docs/QUALITY_BAR.md)

The most important rule:

> Do not turn Tilo into a simple chatbot. Preserve the ROAM Loop: Render, Observe, Act, Memorize.

---

## License

Apache License 2.0
