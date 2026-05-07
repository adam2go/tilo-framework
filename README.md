# Tilo Framework

<p align="center">
  <strong>Build AI-native SaaS agents with the ROAM Loop: Render, Observe, Act, Memorize.</strong>
</p>

<p align="center">
  <a href="./README.zh-CN.md">中文</a> ·
  <a href="./docs/ROAM_LOOP.md">ROAM Loop</a> ·
  <a href="./docs/CONVERSATION_RUNTIME.md">Conversation Runtime</a> ·
  <a href="./docs/MEMORY.md">Memory</a> ·
  <a href="./docs/BUILD_YOUR_FIRST_TILO_APP.md">Build an App</a> ·
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
  <img alt="Tilo Framework overview: AI-native SaaS agent runtime built around the ROAM Loop" src="./docs/assets/tilo-framework-overview.svg" />
</p>

---

## What is Tilo?

**Tilo is an open-source framework for building AI-native SaaS agents that render interactive product surfaces, observe human decisions, act through tools, and memorize confirmed learning.**

Most agent frameworks focus on reasoning, tool calling, workflows, or multi-agent orchestration. Tilo focuses on the missing product layer:

> What if the user interface itself became part of the agent runtime?

Tilo is not a chatbot wrapper. It is an **AI-native SaaS interaction runtime**.

---

## Example Use Cases

### Contract Review Agent

```text
Review this contract and flag risky clauses around liability, termination, and payment terms.
```

Tilo renders risk panels, suggested revisions, approval cards, full review artifacts, and memory candidates.

### Sales Follow-up Agent

```text
Which customers should sales follow up with this week?
```

Tilo renders follow-up recommendations, decision cards, draft actions, and reusable tone preferences.

### Competitive Analysis Agent

```text
Create a competitive analysis for memory-native AI agent frameworks.
```

Tilo can render a comparison matrix, evidence cards, option selection, and follow-up actions.

---

## Try the Demo

```bash
git clone https://github.com/adam2go/tilo-framework.git
cd tilo-framework
cp .env.example .env

docker compose up --build
```

Open:

```text
http://localhost:3000/demo/telegram
```

Health check:

```bash
curl http://localhost:8000/api/health
```

The demo supports deterministic local mode and backend-only LLM mode through OpenAI-compatible configuration. API keys stay in `.env` on the backend and are never exposed to the frontend.

---

## How It Works: ROAM Loop

```text
Render -> Observe -> Act -> Memorize
```

- **Render** — the agent renders an interactive artifact or component surface.
- **Observe** — user clicks, edits, approvals, selections, feedback, and tool results become structured observations.
- **Act** — the agent updates artifacts, invokes tools, asks questions, creates confirmations, or starts follow-up tasks.
- **Memorize** — confirmed decisions, preferences, project facts, and reusable procedures become long-term memory.

ROAM turns UI from a passive display layer into an active part of the agent runtime.

| Traditional agent loop | Tilo ROAM loop |
|---|---|
| Observation is mostly tool output | Observation includes human UI interaction |
| Output is text or tool result | Output can be an interactive artifact |
| UI is outside the loop | UI is part of the loop |
| Memory is optional | Memory closes the loop |

Read more: [`docs/ROAM_LOOP.md`](./docs/ROAM_LOOP.md)

---

## Runtime Primitives

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

Core pieces:

- **Agent App Manifest** — app identity, entry prompt, surfaces, sample inputs, tools, and channels.
- **Interaction Policy** — backend source of truth for when UI should appear.
- **Mini / Rich Surfaces** — inline decision cards and on-demand full artifact surfaces.
- **Conversation Runtime** — durable sessions and turns across web, Telegram, and future channels.
- **UI Observations** — user actions become structured runtime observations.
- **Context Reflection** — ORID-style reflection can turn raw interactions into explainable next actions and memory candidates.
- **Memory Lifecycle** — observations do not become long-term memory until explicitly confirmed.

---

## Build an Agent App

A Tilo app is a small declarative folder:

```text
app.yaml
interaction.policy.yaml
fixtures or sample inputs
optional README
```

Start with:

```text
examples/apps/contract-review-agent/
examples/apps/sales-followup-agent/
```

Create a new app:

```bash
python scripts/create_app.py my-agent
```

Then edit `app.yaml` and `interaction.policy.yaml`. The policy decides when the agent should continue silently, ask a question, show a mini surface, or open a rich surface.

Developer references:

- [`docs/BUILD_YOUR_FIRST_TILO_APP.md`](./docs/BUILD_YOUR_FIRST_TILO_APP.md)
- [`docs/APP_MANIFEST.md`](./docs/APP_MANIFEST.md)
- [`docs/INTERACTION_POLICY.md`](./docs/INTERACTION_POLICY.md)
- [`examples/apps/README.md`](./examples/apps/README.md)

---

## Current Capabilities

- Conversation sessions and turns
- Web demo session restore with `session_id`
- Telegram text/callback mapping foundation
- Backend interaction policy evaluation
- Mini surfaces and rich surface links
- `artifact_spec.v1` artifact rendering foundation
- Memory candidates and confirmation-before-persistence
- ORID-inspired context reflection plan
- Declarative example apps and scaffold script

---

## Roadmap

| Milestone | Focus |
|---|---|
| v0.5 | Durable conversation runtime, rich surface escalation, Telegram mapping, second app |
| v0.6 | ConversationService, typed runtime primitives, centralized observation linkage, developer DX |
| v0.7 | Run-to-session closure, conversation-native message endpoint, ORID reflection, explainable memory candidates |
| Future | MCP, browser/GUI automation, more channel adapters, permissions, skill marketplace primitives |

---

## Repository Map

```text
backend/       FastAPI backend, runtime services, memory, tools, artifacts
frontend/      Next.js console, artifact renderer, memory/trace/inbox panels
docs/          Product principles, ROAM Loop, architecture, guides, implementation plans
evals/         Local benchmark scaffolding
examples/      Declarative agent app examples and fixtures
scripts/       Developer utilities
```

---

## Documentation

- [`docs/ROAM_LOOP.md`](./docs/ROAM_LOOP.md)
- [`docs/CONVERSATION_RUNTIME.md`](./docs/CONVERSATION_RUNTIME.md)
- [`docs/MEMORY.md`](./docs/MEMORY.md)
- [`docs/ARTIFACTS.md`](./docs/ARTIFACTS.md)
- [`docs/SKILLS.md`](./docs/SKILLS.md)
- [`docs/API_CONTRACTS.md`](./docs/API_CONTRACTS.md)
- [`docs/BUILD_YOUR_FIRST_TILO_APP.md`](./docs/BUILD_YOUR_FIRST_TILO_APP.md)
- [`docs/USER_GUIDE.md`](./docs/USER_GUIDE.md)

---

## Contributing

Tilo is early. Contributions are welcome.

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
