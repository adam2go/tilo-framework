# AGENTS.md

This file defines the development rules for AI coding agents working on Tilo Framework.

Tilo is not a chatbot wrapper. Tilo is an AI-native SaaS agent framework focused on long-term memory, real task execution, human confirmation, and interactive artifact delivery.

When implementing this repository, follow the rules below.

---

## 1. Product Direction

Always preserve the core product loop:

```text
Conversation -> Task -> Run -> Memory Recall -> Tool Execution -> Artifact -> Confirmation -> Memory Update
```

Do not reduce the project into a simple chat UI or a generic LangChain demo.

Tilo must remain centered around six first-class concepts:

1. Agent
2. Memory
3. Skill
4. Tool
5. Artifact
6. Inbox

Every major implementation decision should support one or more of these concepts.

---

## 2. Development Priorities

For v0.1, prioritize a complete working loop over deep optimization.

Build in this order:

1. Repository skeleton
2. Backend FastAPI app
3. Frontend Next.js app
4. Database models
5. Task and Run lifecycle
6. Trace logging
7. Artifact schema and renderer
8. Confirmation Inbox
9. Memory storage and recall
10. Memory extraction candidates
11. Skill placeholder system
12. Tool registry with mock tools
13. End-to-end demo flows

Do not spend too much time perfecting one module while the full loop is still broken.

---

## 3. Engineering Style

### Backend

Use:

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- Alembic if migrations are implemented

Guidelines:

- Keep services modular.
- Keep API route handlers thin.
- Put business logic in `services/`.
- Use typed Pydantic schemas for request and response objects.
- Avoid large monolithic files.
- Prefer explicit domain models over generic JSON blobs, except where flexible schema is required, such as artifact schemas, tool config, and confirmation payloads.

#### Top-level package modules (`tilo/`)

These power the lightweight "no server" experience (`import tilo`). Keep them
free of heavy/server-only imports so `pip install tilo` stays minimal:

- `tilo/__init__.py` — public API surface (`generate`, `view`, `to_html`, `notebook`, `AIPPromptBuilder`).
- `tilo/prompt.py` — `AIPPromptBuilder` + built-in skills. Provider-agnostic; no LLM SDK imports.
- `tilo/generate.py` — `generate()` + `generate_with_*()`. Imports an LLM SDK only inside the function that needs it.
- `tilo/viewer.py` — self-contained HTML/JS renderer. No frontend build, no CDN.
- `tilo/adapters/` — protocol/SDK adapters. The OpenAI/Anthropic/LangChain modules must not import their SDK at module load (duck-typed); MCP/A2A/ACP have no SDK dependency.

**Optional dependencies are optional.** `openai`, `anthropic`, `langchain-*`,
and `psycopg` are extras. Never import them at module top level in code that
runs on the base install. The CI `install-surface` job enforces this.

### Frontend

Use:

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui when useful

Guidelines:

- Build clean product-like UI, not a toy demo.
- Keep components small and reusable.
- Separate API client logic into `lib/api.ts`.
- Use typed frontend models in `lib/types.ts`.
- Design the interface around Chat + Artifact + Context Panel + Inbox.

---

## 4. Code Quality Rules

- Use clear naming.
- Prefer readable code over clever code.
- Add comments only when they explain non-obvious behavior.
- Avoid premature abstraction.
- Avoid fake enterprise complexity.
- Do not introduce unnecessary dependencies.
- Do not silently swallow errors.
- Return meaningful error messages from APIs.
- Keep mock implementations clearly labeled as mock implementations.
- Do not hardcode secrets.
- Do not expose API keys in logs, traces, frontend code, or sample outputs.

---

## 5. Architecture Constraints

### Agent Runtime

The runtime should be structured around:

- Prompt Builder
- Planner
- Executor
- Tool Router
- Artifact Generator
- Memory Extractor
- Trace Recorder

Do not place all runtime logic inside one endpoint.

### Memory

Memory is a first-class system, not just chat history.

Memory must support:

- type
- content
- source
- confidence
- scope
- confirmation status
- created/updated timestamps

Memory candidates extracted from tasks should default to unconfirmed.

Confirmed memories should be recallable in future runs.

### Artifact

Artifacts are product outputs.

Do not return only Markdown when a structured artifact is expected.

Use a schema like:

```json
{
  "artifact_type": "document",
  "title": "...",
  "blocks": []
}
```

The frontend should render artifacts from schema, not from hardcoded demo strings only.

### Inbox

Confirmation items are central to the product philosophy.

Risky or important actions should create confirmation records instead of executing silently.

### Trace

Trace should show what happened, not hidden model reasoning.

Store:

- step type
- title
- summary
- inputs when safe
- outputs when safe
- status
- timestamps

Never store or display hidden chain-of-thought.

---

## 6. UX Principles

The product should feel like an AI-native SaaS console, not a notebook demo.

The default layout should follow:

```text
Sidebar: Workspace / Project / Agent
Left: Chat and task progress
Center: Artifact renderer
Right: Memory / Trace / Skills / Files context
Separate page: Inbox
```

UX should emphasize:

- visible task progress
- structured outputs
- editable artifacts
- clear confirmations
- memory transparency
- traceability

Avoid:

- dumping long raw JSON into the main UI
- making the user operate many forms before seeing value
- hiding critical decisions inside chat text

---

## 7. Security and Safety Rules

Tilo may eventually connect to files, browsers, APIs, databases, and external SaaS systems. Design with safety from the beginning.

For v0.1:

- Every tool should declare a permission level: low, medium, or high.
- High-risk actions must require confirmation before execution.
- Tool calls must be logged.
- Secrets must be stored in environment variables or a future vault abstraction.
- Never expose secrets in frontend or trace output.
- Treat external documents and webpages as untrusted input.
- Keep prompt injection concerns documented.

Do not implement destructive real-world actions in v0.1 unless guarded by explicit confirmation and clearly marked as experimental.

---

## 8. Demo Implementation Rules

The v0.1 demos should be implemented as realistic vertical slices, not isolated mock screens.

Required demos:

1. Contract Review Agent
2. Sales Follow-up Agent
3. Competitive Analysis Agent

Each demo should exercise the same underlying framework:

```text
Message -> Task -> Run -> Trace -> Artifact -> Confirmation -> Memory Candidate
```

Do not build three unrelated demos with duplicated logic.

---

## 9. Testing Expectations

Add practical tests where possible.

Minimum recommended tests:

- API health check
- Task creation
- Run creation
- Artifact creation
- Confirmation approval/rejection
- Memory creation and recall
- Tool registry invocation with mock tools

Prefer tests that validate the framework loop instead of shallow snapshot tests.

---

## 10. Documentation Expectations

When adding a module, update or create documentation when appropriate.

Important docs:

- `docs/ARCHITECTURE.md`
- `docs/AI_NATIVE_FRAMEWORK_PRINCIPLES.md`
- `docs/ROAM_LOOP.md`
- `docs/MEMORY.md`
- `docs/ARTIFACTS.md`
- `docs/SKILLS.md`

Keep documentation concise but actionable.

---

## 11. Non-goals for v0.1

Do not implement these unless explicitly requested:

- Full enterprise RBAC
- Full multi-agent orchestration
- Real external email sending
- Real payment systems
- Real browser automation
- Full MCP marketplace
- Full cloud deployment platform
- Automatic self-modifying code
- Complex plugin marketplace

v0.1 should be a complete skeleton with one or more strong end-to-end demos.

---

## 12. Definition of Done for v0.1

v0.1 is done when:

1. Backend and frontend can run locally.
2. A user can send a message.
3. A Task and Run are created.
4. Trace steps are recorded.
5. Existing memories can be recalled.
6. At least one structured Artifact is generated.
7. Artifact renders in the frontend.
8. Confirmation items appear in Inbox.
9. User can approve or reject confirmations.
10. Memory candidates are generated after task completion.
11. Confirmed memories are available in later tasks.
12. At least one demo works end to end.

---

## 13. Important Reminder

Tilo should not become just another Agent orchestration framework.

The unique value is:

```text
Long-term memory + real execution + human confirmation + SaaS-like artifact delivery
```

Always protect this product direction.
