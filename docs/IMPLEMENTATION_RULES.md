# Implementation Rules

This document defines concrete implementation rules for Tilo Framework.

These rules are intended for Codex, Claude Code, and human contributors.

If a product principle describes "what Tilo should be", this document describes "how Tilo should be implemented".

## 1. Required Language and Runtime Versions

Use these defaults unless explicitly changed by maintainers.

### Backend

- Language: Python
- Python version: 3.11+
- Framework: FastAPI
- ORM: SQLAlchemy 2.x style
- Validation: Pydantic v2
- Database: PostgreSQL
- Vector extension: pgvector when available
- Cache/queue: Redis when needed

### Frontend

- Language: TypeScript
- Framework: Next.js
- React: 18+
- Styling: Tailwind CSS
- UI components: shadcn/ui when useful
- Icons: lucide-react

### Package Management

Preferred defaults:

- Backend: `uv` or `pip` with `pyproject.toml`
- Frontend: `pnpm`

If the implementation chooses another package manager, document the reason in README.

## 2. Repository Structure Rules

The repository should follow this structure:

```text
backend/
  app/
    main.py
    core/
    api/
    models/
    schemas/
    services/
    workers/
  tests/
  pyproject.toml
  Dockerfile

frontend/
  app/
  components/
  lib/
  styles/
  package.json
  Dockerfile

docs/
  *.md

docker-compose.yml
.env.example
README.md
AGENTS.md
CONTRIBUTING.md
LICENSE
```

Do not place backend and frontend implementation code directly in the repository root.

## 3. Backend Implementation Rules

### 3.1 Route Handlers

Route handlers must be thin.

Allowed in route handlers:

- request parsing
- dependency injection
- calling services
- returning responses

Not allowed in route handlers:

- complex runtime orchestration
- memory extraction logic
- artifact generation logic
- tool execution logic
- large business workflows

### 3.2 Services

Business logic belongs in `backend/app/services/`.

Recommended service modules:

```text
services/agent_runtime/
services/memory/
services/artifact/
services/skill/
services/tools/
services/inbox/
services/message_gateway/
```

### 3.3 Models and Schemas

- Database models belong in `models/`.
- Pydantic schemas belong in `schemas/`.
- Use explicit schemas for request and response bodies.
- Avoid untyped `dict` everywhere.

### 3.4 JSON Fields

JSON fields are allowed for flexible data such as:

- artifact schema
- tool config
- confirmation payload
- skill input/output schemas
- run plan

Do not use JSON fields to avoid modeling core domain concepts.

## 4. Frontend Implementation Rules

### 4.1 UI Layout

The default frontend should support:

```text
Sidebar | Chat / Task Panel | Artifact Panel | Context Panel
```

And a separate Inbox page.

Do not implement only a centered chatbot UI.

### 4.2 Components

Use reusable components.

Recommended directories:

```text
components/layout/
components/chat/
components/artifact/
components/memory/
components/trace/
components/inbox/
components/skills/
```

### 4.3 API Client

Frontend API calls should go through `frontend/lib/api.ts`.

Shared frontend types should live in `frontend/lib/types.ts`.

Do not scatter raw fetch calls throughout components.

### 4.4 Artifact Rendering

Artifact UI must be schema-driven.

Use a central `ArtifactRenderer` that dispatches by:

- `artifact_type`
- `block.type`

Avoid hardcoding demo-only artifact HTML that cannot render future artifact types.

## 5. Domain Integrity Rules

Do not bypass core domain objects.

Every user goal should become:

```text
Task -> Run -> TraceStep(s)
```

Every meaningful output should become:

```text
Artifact
```

Every human decision should become:

```text
Confirmation
```

Every long-term learned fact should become:

```text
Memory candidate -> confirmed Memory
```

Demos must use these primitives.

## 6. Runtime Implementation Rules

The Agent Runtime should be composed of these services:

- RunManager
- MemoryRecallService
- SkillSelector
- PromptBuilder
- Planner
- Executor
- ToolRegistry
- ArtifactGenerator
- ConfirmationService
- MemoryExtractionService
- TraceRecorder

Do not implement the runtime as one giant function.

For v0.1, simple rule-based or mock implementations are acceptable if the architecture is preserved.

## 7. Tool Implementation Rules

Every tool must have:

- id
- name
- type
- description
- config
- permission_level

Permission levels:

- low
- medium
- high

High-risk tools must create a Confirmation before execution.

All tool calls must create TraceStep records.

## 8. Memory Implementation Rules

Memory must be structured and inspectable.

Generated memory candidates must default to:

```text
is_confirmed = false
```

Only confirmed memories should be used for future personalized recall.

Do not store hidden chain-of-thought as memory.

Do not store secrets as memory.

## 9. Artifact Implementation Rules

Artifact schema must use this shape:

```json
{
  "artifact_type": "document",
  "title": "Artifact title",
  "blocks": []
}
```

Supported v0.1 artifact types:

- document
- table
- dashboard
- kanban
- timeline
- contract_review

Supported v0.1 block types:

- markdown
- table
- card
- metric
- list
- kanban
- timeline
- risk_item
- confirmation_action

## 10. Error Handling Rules

- Do not silently swallow errors.
- Return meaningful API errors.
- Log backend errors safely.
- Never log secrets.
- Keep user-facing errors understandable.

## 11. Security Rules

- No secrets in Git.
- No secrets in frontend code.
- No secrets in trace output.
- No hidden chain-of-thought in trace output.
- Treat uploaded documents and web content as untrusted input.
- Confirmation-gate high-risk actions.

## 12. Dependency Rules

Before adding a dependency, check:

1. Is it actively maintained?
2. Does it reduce meaningful complexity?
3. Does it preserve Tilo's domain model?
4. Can the project still run locally with Docker Compose?

Avoid adding heavy dependencies for minor convenience.

## 13. Local Development Requirements

The project should support local development with:

```text
docker-compose up
```

At minimum, provide:

- `.env.example`
- backend startup command
- frontend startup command
- database setup notes

## 14. Testing Rules

Backend should use pytest.

Minimum test coverage targets for v0.1:

- health endpoint
- task creation
- run creation
- trace creation
- artifact creation
- confirmation approval/rejection
- memory creation/confirmation/recall
- mock tool invocation

Frontend should at least pass TypeScript checks.

## 15. Documentation Rules

If an implementation changes architecture or core behavior, update the relevant document:

- architecture changes -> `docs/ARCHITECTURE.md`
- memory changes -> `docs/MEMORY.md`
- artifact changes -> `docs/ARTIFACTS.md`
- skill changes -> `docs/SKILLS.md`
- API changes -> `docs/API_CONTRACTS.md`
- security changes -> `docs/SECURITY.md`

## 16. Anti-patterns

Do not:

- build only a chatbot
- store all outputs as Markdown
- store memory as raw chat history only
- put all runtime logic in one endpoint
- bypass Task/Run/Artifact/Confirmation/Memory
- create disconnected mock pages
- leak secrets
- expose hidden model reasoning
- add unnecessary dependencies
- optimize one subsystem before the end-to-end loop works

## 17. Final Rule

When in doubt, choose the implementation that best preserves:

```text
Long-term memory + real execution + structured artifacts + human confirmation + future improvement
```
