# Tilo Framework

**Build agents that remember, act, and deliver AI-native apps.**

Tilo Framework is an open-source framework for building memory-native, self-improving AI agents that can execute real work and deliver SaaS-like interactive artifacts.

> Stop building chatbots. Start building AI-native agents that remember context, act through tools, and present outcomes as usable products.

## Why Tilo

Most Agent frameworks focus on tool calling, workflows, or multi-agent orchestration. Tilo focuses on a different question:

**How can an agent continuously understand a user or project, execute work over time, and deliver results through product-like interfaces instead of plain chat messages?**

Tilo is designed around six core concepts:

| Concept | Description |
|---|---|
| Agent | Understands goals, plans tasks, invokes tools, and coordinates execution. |
| Memory | Stores long-term user, project, task, and procedural knowledge. |
| Skill | Encapsulates reusable methods, templates, instructions, and optional executable code. |
| Tool | Connects agents to external systems such as files, APIs, browsers, MCP servers, and databases. |
| Artifact | Turns agent outputs into editable documents, tables, dashboards, kanban boards, review panels, and lightweight SaaS-like interfaces. |
| Inbox | Collects human decisions, confirmations, approvals, and follow-up actions. |

## Core Philosophy

### Conversation as Command

Users should be able to describe goals naturally. The framework turns those goals into structured agent tasks.

### Artifact as Product

Agent outputs should not stop at Markdown. They should become interactive, editable, shareable artifacts.

### Human as Decision Maker

Humans should not operate every step of a SaaS workflow. They should confirm key decisions, approve risky actions, and refine outcomes.

### Memory-first Agents

Long-term memory is a first-class capability. Agents should remember users, projects, decisions, preferences, and reusable patterns.

### Self-improving Loop

After each task, the system should extract useful memories, propose skill improvements, and make future runs better.

## v0.2 Scope

Tilo v0.2 implements a complete but lightweight framework loop:

```text
User message
  -> Create task
  -> Recall memory
  -> Plan execution
  -> Invoke tools
  -> Generate artifact
  -> Ask for confirmation when needed
  -> Complete task
  -> Extract memory candidates
  -> Update memory after approval
```

Current v0.2 foundations include:

- Structured memory candidates, recall events, write events, confirmation, rejection, editing, and deletion.
- `artifact_spec.v1` with schema validation, renderer registry, durable artifact detail pages, actions, provenance, and memory refs.
- Safe self-improvement primitives: run metrics, feedback, skill candidates, approval, rejection, and promotion.
- Run state transitions, trace sanitization, failed-run handling, and a persisted tool invocation ledger.
- High-risk tool invocations create durable Confirmation records instead of executing silently.
- Local eval scaffolding for memory recall, artifact schema validity, and the end-to-end runtime loop.

## Recommended Tech Stack

| Layer | Recommendation |
|---|---|
| Backend | Python + FastAPI |
| Frontend | Next.js + React + TypeScript + Tailwind CSS + shadcn/ui |
| Database | PostgreSQL + pgvector |
| Cache / Queue | Redis |
| Model API | OpenAI-compatible API |
| Deployment | Docker Compose for v0.1 |

## Planned Modules

- Tilo Runtime
- Tilo Memory
- Tilo Skills
- Tilo Tools
- Tilo Artifacts
- Tilo Inbox
- Tilo Gateway
- Tilo Console

## Killer Demos

The first version should prioritize three high-signal demos:

1. **Contract Review Agent**  
   Upload a contract, detect risks, highlight clauses, generate suggestions, and create a review artifact.

2. **Sales Follow-up Agent**  
   Analyze customer records, generate follow-up recommendations, and ask the user to confirm the next action.

3. **Competitive Analysis Agent**  
   Generate a structured competitor report with summary cards, comparison tables, and recommendations.

## Documentation

See [`docs/CODEX_SPEC.md`](docs/CODEX_SPEC.md) for the initial development specification.

For v0.2 implementation details, see:

- [`docs/V0_2_AUDIT.md`](docs/V0_2_AUDIT.md)
- [`docs/V0_2_CODEX_PLAN.md`](docs/V0_2_CODEX_PLAN.md)
- [`docs/V0_2_RELEASE_NOTES.md`](docs/V0_2_RELEASE_NOTES.md)
- [`evals/README.md`](evals/README.md)

## Local Development

Run the full stack with Docker Compose:

```bash
docker compose up --build
```

Backend health:

```bash
curl http://localhost:8000/api/health
```

Frontend console:

```text
http://localhost:3000
```

Run local evals:

```bash
python3 evals/runners/run_memory_recall_eval.py
python3 evals/runners/run_artifact_schema_eval.py
python3 evals/runners/run_runtime_loop_eval.py
```

## License

Apache License 2.0
