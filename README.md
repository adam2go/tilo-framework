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
  <a href="./docs/CONVERSATION_RUNTIME.md">Conversation Runtime</a> ·
  <a href="./docs/MEMORY.md">Memory</a> ·
  <a href="./docs/USER_GUIDE.md">User Guide</a>
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

<p align="center">
  <img alt="Tilo Framework hero: AI-native SaaS interaction runtime" src="./docs/assets/tilo-framework-hero.png" />
</p>

---

## What is Tilo?

**Tilo is an open-source framework for building AI-native SaaS agents that can render interactive product surfaces, observe human decisions, act through tools, and memorize confirmed learning.**

Most agent frameworks focus on reasoning, tool calling, workflow orchestration, or multi-agent coordination.

Tilo focuses on a different question:

> What if the user interface itself became part of the agent runtime?

In Tilo, an agent does not only produce text or call tools. It can render SaaS-like artifacts, observe how users approve, edit, select, reject, and refine those artifacts, continue acting on those observations, and turn confirmed learning into long-term memory.

Tilo is not a chatbot wrapper. It is an **AI-native SaaS interaction runtime**.

---

## The Core Idea: ROAM Loop

Tilo introduces the **ROAM Loop**:

```text
Render -> Observe -> Act -> Memorize
```

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

That means common SaaS components can become agent-generated interaction components:

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

## Runtime Architecture

```text
Agent App Manifest
        ↓
Interaction Policy
        ↓
Mini / Rich Surface
        ↓
UIInteractionEvent
        ↓
ConversationTurn(observation)
        ↓
AgentContextBuilder
        ↓
PromptBuilder
        ↓
Agent Runtime
        ↓
Memory Candidate -> Human Confirmation -> Confirmed Memory
```

Tilo is built around a few runtime primitives:

- **Agent App Manifest** — declarative app identity, entry prompt, surfaces, sample inputs, tools, and channels.
- **Interaction Policy** — backend source of truth for when the agent should continue silently, ask text, show a mini surface, or open a rich surface.
- **Mini Surface Registry** — inline decision cards rendered inside the conversation.
- **Rich Surface Link** — on-demand artifact escalation for full pages, drawers, or webviews.
- **Conversation Runtime** — durable sessions and turns across web, Telegram, and future channels.
- **UI Observations** — user actions become structured runtime observations.
- **Context Reflection** — ORID-style reflection can turn raw interactions into explainable next actions and memory candidates.
- **Memory Lifecycle** — observations do not become long-term memory until explicitly confirmed.

---

## Current Capabilities

### Conversation-first runtime

- `ConversationSession` and `ConversationTurn`
- Web demo session restore through `session_id`
- Telegram text/callback mapping
- Append-only durable turns
- Channel-friendly runtime model

### ROAM-native interaction layer

- Mini surfaces inside conversation
- Rich surface escalation
- UIInteractionEvent persistence
- Observation turns linked to interactions
- Backend interaction policy evaluation

### Artifact delivery

- `artifact_spec.v1`
- Schema-driven rendering
- Renderer registry
- Artifact actions
- State bindings
- Confirmation-aware actions

### Memory and context

- Structured memory records
- Memory candidates
- User confirmation before persistence
- Workspace/project scoped recall
- Memory recall/write events
- ORID-inspired context reflection plan

### Developer experience

- Declarative example apps
- App manifest loader
- Policy surface validation
- Sales Follow-up second example app
- Tiny app scaffold script
- Local eval scaffolding

---

## Public Demo

Run the Telegram-like ROAM showcase:

```bash
docker compose up --build
```

Then open:

```text
http://localhost:3000/demo/telegram
```

The demo supports deterministic local mode and backend-only LLM mode through OpenAI-compatible configuration. API keys stay in `.env` on the backend and are never exposed to the frontend.

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

## Build an Agent App

Tilo apps can be defined declaratively instead of hard-coded into one demo.

Start with the contract review example:

```text
examples/apps/contract-review-agent/app.yaml
examples/apps/contract-review-agent/interaction.policy.yaml
```

A Tilo app usually contains:

```text
app.yaml
interaction.policy.yaml
fixtures or sample inputs
optional README
```

The manifest defines the app entry prompt, runtime fallback behavior, allowed mini/rich surfaces, sample inputs, tools, and channels. The policy decides when the agent should continue with `no_ui`, show a `mini_surface`, open a `rich_surface`, or `ask_text`.

To add a new app:

1. Copy `examples/apps/contract-review-agent/` or run `python scripts/create_app.py my-agent`.
2. Change `app.yaml` identity, entry prompt, surfaces, sample inputs, tools, and channels.
3. Edit `interaction.policy.yaml` so UI appears only at meaningful decision points.
4. Open `GET /api/apps` to confirm the manifest loads.
5. Reuse or add mini surfaces through the frontend mini surface registry.

Developer references:

- [`docs/APP_MANIFEST.md`](./docs/APP_MANIFEST.md)
- [`docs/INTERACTION_POLICY.md`](./docs/INTERACTION_POLICY.md)
- [`docs/MINI_SURFACE_REGISTRY.md`](./docs/MINI_SURFACE_REGISTRY.md)
- [`docs/BUILD_YOUR_FIRST_TILO_APP.md`](./docs/BUILD_YOUR_FIRST_TILO_APP.md)
- [`examples/apps/README.md`](./examples/apps/README.md)

---

## Example Use Cases

### Contract Review Agent

```text
Review this contract and flag risky clauses around liability, termination, and payment terms.
```

Tilo renders a contract review surface with risk panels, suggested revisions, approval cards, and memory candidates.

### Sales Follow-up Agent

```text
Which customers should sales follow up with this week?
```

Tilo renders customer follow-up recommendations, a decision card, draft actions, and preference memory candidates.

### Competitive Analysis Agent

```text
Create a competitive analysis for memory-native AI agent frameworks.
```

Tilo can render a comparison matrix with option picking, evidence cards, and follow-up actions.

---

## Project Status

Tilo is still early, but it is moving from a demo toward a real open-source agent app runtime.

| Area | Status |
|---|---|
| ROAM Loop concept | Documented |
| Artifact spec v1 | Working foundation |
| Conversation runtime | Working foundation |
| UI observations | Working foundation |
| Agent context bridge | Working foundation |
| Interaction policy | Working foundation |
| Rich surface escalation | Working foundation |
| Memory candidates | Working foundation |
| Telegram mapping | Early foundation |
| ORID context reflection | Planned / in progress |
| UI polish | Needs improvement |

---

## Roadmap

### v0.5: Conversation Runtime and Multi-app

- Durable conversation sessions and turns
- Session-aware agent context
- Rich surface escalation
- Telegram mapping
- Sales Follow-up example app

### v0.6: Runtime Hardening and Developer Experience

- ConversationService
- Typed runtime primitives
- Centralized observation linkage
- Better prompt context shape
- Developer app guide and scaffold script

### v0.7: ORID Context Reflection and Runtime Closure

- Run-to-session context closure
- Conversation-native message endpoint
- UIInteractionEvent to observation turn automation
- ORID-style context reflection
- Explainable memory candidates

### Future

- MCP integration
- Browser and GUI automation
- Artifact sharing and publishing
- Slack / Discord / WeChat-style adapters
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
examples/      Declarative agent app examples and fixtures
scripts/       Small developer utilities
```

---

## Documentation

- [`docs/ROAM_LOOP.md`](./docs/ROAM_LOOP.md) — Tilo's core interaction loop
- [`docs/AI_NATIVE_INTERACTION_COMPONENTS.md`](./docs/AI_NATIVE_INTERACTION_COMPONENTS.md) — AI-native SaaS component system
- [`docs/ROAM_INTERACTION_CONTRACT.md`](./docs/ROAM_INTERACTION_CONTRACT.md) — ROAM interaction contract
- [`docs/CONVERSATION_RUNTIME.md`](./docs/CONVERSATION_RUNTIME.md) — conversation runtime
- [`docs/MEMORY.md`](./docs/MEMORY.md) — memory system design
- [`docs/ARTIFACTS.md`](./docs/ARTIFACTS.md) — artifact protocol
- [`docs/SKILLS.md`](./docs/SKILLS.md) — skill system
- [`docs/API_CONTRACTS.md`](./docs/API_CONTRACTS.md) — API contracts
- [`docs/BUILD_YOUR_FIRST_TILO_APP.md`](./docs/BUILD_YOUR_FIRST_TILO_APP.md) — build your first Tilo app
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
