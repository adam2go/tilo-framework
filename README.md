# Tilo Framework

<p align="center">
  <strong>Build agents that remember, improve, and deliver AI-native apps.</strong>
</p>

<p align="center">
  <a href="./README.zh-CN.md">中文</a> ·
  <a href="./docs/USER_GUIDE.md">User Guide</a> ·
  <a href="./docs/V0_2_RELEASE_NOTES.md">v0.2 Notes</a> ·
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

**Tilo is an open-source framework for building memory-native, self-improving AI agents that can execute real work and deliver SaaS-like interactive result pages.**

Most agent frameworks focus on tool calling, orchestration, or multi-agent workflows. Tilo focuses on a different question:

> What if an agent could remember long-term context, improve through feedback, execute real tasks, and deliver the final result as an interactive product page instead of a chat message?

Tilo is not a chatbot wrapper. It is an **AI-native SaaS agent framework**.

```text
Conversation
  -> Task
  -> Run
  -> Memory Recall
  -> Skill Selection
  -> Tool Execution
  -> Artifact Generation
  -> Human Confirmation
  -> Memory Update
  -> Future Improvement
```

---

## Why Tilo?

Traditional SaaS asks users to operate software:

```text
Open app -> find feature -> fill form -> click buttons -> inspect result -> decide next step
```

Tilo is designed for AI-native software:

```text
Describe goal -> agent executes -> result page appears -> human confirms key decisions
```

The UI does not disappear. It changes role:

- Chat becomes the command layer.
- Agent runtime becomes the execution layer.
- Memory becomes the continuity layer.
- Artifact pages become the product delivery layer.
- Inbox becomes the human decision layer.

---

## Core Features

### 1. Long-term Memory

Tilo treats memory as a first-class system, not raw chat history.

- Structured memory records
- Memory candidates
- User confirmation before long-term persistence
- Workspace/project scoped recall
- Memory recall events
- Memory write events
- Future-ready embedding and rerank support

### 2. Agent Self-improvement

Tilo introduces safe self-improvement primitives.

- Run metrics
- Feedback records
- Skill candidates
- Human review before skill promotion
- Eval scaffolding
- No unsafe self-modification by default

### 3. AI-native Artifact Delivery

Agent outputs should become usable products.

- `artifact_spec.v1`
- Schema-driven artifact rendering
- Durable artifact pages
- Renderer registry
- Artifact actions
- Confirmation-aware actions
- Provenance and memory references

### 4. Human Decision Inbox

Humans should approve important decisions, not operate every workflow step.

- Durable confirmations
- Approve / reject / edit flows
- High-risk tool gates
- Pending decision queue

### 5. Traceable Runtime

Every run produces visible, safe execution traces.

- Task and Run lifecycle
- Trace steps
- Sanitized trace output
- Failed-run handling
- Tool invocation ledger

### 6. Local-first Developer Experience

Tilo is built to run locally first.

- Docker Compose stack
- FastAPI backend
- Next.js frontend
- PostgreSQL + pgvector
- Redis
- Local eval runners

---

## Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                    Tilo Console                         │
│  Chat / Artifact / Memory / Trace / Skills / Inbox      │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│                      API Layer                          │
│ Workspaces / Projects / Agents / Messages / Runs        │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│                    Agent Runtime                        │
│ RunManager / StateMachine / Planner / Executor          │
└──────────────┬─────────────┬───────────────┬────────────┘
               │             │               │
┌──────────────▼───┐ ┌───────▼───────┐ ┌────▼─────────────┐
│ Memory Engine    │ │ Skill System  │ │ Tool Registry    │
│ Recall / Events  │ │ Candidates    │ │ Permission Gate  │
└──────────────┬───┘ └───────┬───────┘ └────┬─────────────┘
               │             │              │
┌──────────────▼─────────────▼──────────────▼─────────────┐
│                  Artifact + Inbox Layer                  │
│ ArtifactSpec v1 / Renderer Registry / Confirmations      │
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

The current UI is a single AI-native console page.

1. Open `http://localhost:3000`.
2. Pick one of the demo prompts or type your own task.
3. Click **Send Message**.
4. Tilo creates a Task and Run.
5. The center panel renders the generated Artifact.
6. The right panel shows Trace, Memory, Skills, Files, and Inbox.
7. Open **Memory** to confirm useful memory candidates.
8. Open **Inbox** to approve pending confirmations.
9. Run a new task and confirmed memories can be recalled.

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

Tilo generates a contract review artifact with risk items, suggested revisions, and confirmation actions.

### Sales Follow-up Agent

```text
Which customers should sales follow up with this week?
```

Tilo generates a dashboard-style artifact and creates human confirmation items for recommended actions.

### Competitive Analysis Agent

```text
Create a competitive analysis for memory-native AI agent frameworks.
```

Tilo generates a structured comparison artifact instead of a plain text answer.

---

## Project Status

Tilo is currently in early v0.2 development.

| Area | Status |
|---|---|
| Runtime loop | Working foundation |
| Memory candidates | Working foundation |
| Recall / write events | Working foundation |
| Artifact spec v1 | Working foundation |
| Renderer registry | Working foundation |
| Human confirmation | Working foundation |
| Tool permission gate | Working foundation |
| Self-improvement primitives | Early foundation |
| Evals | Local scaffolding |
| UI polish | Needs major improvement |

The current UI is functional but intentionally early. See [`docs/UI_IMPROVEMENT_PLAN.md`](./docs/UI_IMPROVEMENT_PLAN.md).

---

## Roadmap

### v0.2

- Stronger memory governance
- Better artifact result pages
- Skill candidate review flow
- Run metrics and feedback loop
- Tool invocation ledger
- Local eval baseline
- UI onboarding and visual polish

### v0.3

- Hybrid semantic memory recall
- Artifact version history and patching
- Better skill packaging
- MCP tool integration
- File-backed contract review
- More realistic vertical demos

### v0.4+

- Message gateways: Telegram, Slack, Discord, WeChat-style adapters
- Browser and GUI automation
- Artifact sharing and publishing
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
docs/          Product principles, architecture, v0.2 plan, user guide, implementation rules
evals/         Local benchmark scaffolding for memory, artifact, and runtime loop
```

---

## Documentation

- [`docs/PROJECT_CONSTITUTION.md`](./docs/PROJECT_CONSTITUTION.md) — project constitution
- [`docs/PRODUCT_PRINCIPLES.md`](./docs/PRODUCT_PRINCIPLES.md) — product philosophy
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — system architecture
- [`docs/MEMORY.md`](./docs/MEMORY.md) — memory system design
- [`docs/ARTIFACTS.md`](./docs/ARTIFACTS.md) — artifact protocol
- [`docs/SKILLS.md`](./docs/SKILLS.md) — skill system
- [`docs/API_CONTRACTS.md`](./docs/API_CONTRACTS.md) — API contracts
- [`docs/USER_GUIDE.md`](./docs/USER_GUIDE.md) — user guide
- [`docs/UI_IMPROVEMENT_PLAN.md`](./docs/UI_IMPROVEMENT_PLAN.md) — UI improvement plan

---

## Contributing

Tilo is still early, but contributions are welcome.

Before contributing, please read:

- [`AGENTS.md`](./AGENTS.md)
- [`CONTRIBUTING.md`](./CONTRIBUTING.md)
- [`docs/PROJECT_CONSTITUTION.md`](./docs/PROJECT_CONSTITUTION.md)
- [`docs/QUALITY_BAR.md`](./docs/QUALITY_BAR.md)

The most important rule:

> Do not turn Tilo into a simple chatbot. Preserve the loop: memory + execution + artifact + confirmation + improvement.

---

## License

Apache License 2.0
