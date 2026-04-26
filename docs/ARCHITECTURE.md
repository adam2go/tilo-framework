# Architecture

This document defines the target architecture for Tilo Framework v0.1.

## 1. Architectural Goal

Tilo should be implemented as a modular AI-native SaaS agent framework.

The architecture should make these capabilities first-class:

- Agent runtime
- Long-term memory
- Tool execution
- Skill system
- Artifact generation and rendering
- Human confirmation inbox
- Trace and observability
- Message gateway

## 2. High-level System

```text
Web Console
  -> API Layer
  -> Agent Runtime
  -> Memory Engine
  -> Skill System
  -> Tool System
  -> Artifact Engine
  -> Inbox / Confirmation Service
  -> Storage Layer
```

## 3. Backend Modules

Recommended backend structure:

```text
backend/app/
  main.py
  core/
    config.py
    database.py
    security.py
    logging.py
  api/routes/
    workspaces.py
    projects.py
    agents.py
    tasks.py
    runs.py
    memories.py
    artifacts.py
    confirmations.py
    skills.py
    tools.py
    messages.py
  models/
  schemas/
  services/
    agent_runtime/
    memory/
    artifact/
    skill/
    tools/
    inbox/
    message_gateway/
  workers/
```

## 4. Service Boundaries

### API Routes

Routes should be thin. They should:

- Validate input.
- Call services.
- Return typed responses.

They should not contain complex business logic.

### Services

Services own business logic.

Important services:

- `RunManager`
- `PromptBuilder`
- `Planner`
- `Executor`
- `TraceRecorder`
- `MemoryRecallService`
- `MemoryExtractionService`
- `ArtifactGenerator`
- `ConfirmationService`
- `ToolRegistry`
- `SkillSelector`

### Models

Models should represent durable domain objects.

Avoid storing everything as unstructured JSON. Use explicit columns for important fields.

Flexible JSON is acceptable for:

- artifact schema
- tool config
- confirmation payload
- skill input/output schemas
- run plan

## 5. Agent Runtime

The runtime should be composed of these parts:

```text
RunManager
  -> MemoryRecallService
  -> SkillSelector
  -> PromptBuilder
  -> Planner
  -> Executor
  -> ToolRegistry
  -> ArtifactGenerator
  -> ConfirmationService
  -> MemoryExtractionService
  -> TraceRecorder
```

Do not implement all runtime logic inside a single endpoint or a single giant function.

## 6. Runtime Flow

```text
1. Message received
2. Task created
3. Run created
4. Relevant memories recalled
5. Candidate skills selected
6. Prompt built
7. Plan generated
8. Steps executed
9. Tool calls recorded
10. Artifact generated
11. Confirmation created if needed
12. Run completed
13. Memory candidates extracted
14. User confirms memory
15. Confirmed memory becomes recallable
```

## 7. Storage Choices

For v0.1:

- PostgreSQL for primary data
- pgvector for memory embeddings
- Redis for cache/queue if needed
- Local file storage for uploads if implemented

Do not introduce complex infrastructure unless necessary.

## 8. Frontend Architecture

Recommended frontend structure:

```text
frontend/
  app/
    page.tsx
    workspaces/
    projects/
    agents/
    inbox/
    memories/
    skills/
    artifacts/
  components/
    layout/
    chat/
    artifact/
    memory/
    trace/
    inbox/
    skills/
  lib/
    api.ts
    types.ts
```

## 9. Default UI Layout

```text
Sidebar: Workspace / Project / Agent navigation
Left panel: Chat and task progress
Center panel: Artifact renderer
Right panel: Memory / Trace / Skills / Files context
Separate page: Inbox
```

## 10. Important Architecture Constraints

- Artifact rendering must be schema-driven.
- Memory must not be implemented as only chat history.
- Confirmation must be represented as a durable object.
- Trace must not expose hidden chain-of-thought.
- Tool calls must go through ToolRegistry.
- Demos must reuse framework primitives, not duplicated one-off code.

## 11. Suggested Framework Dependencies

Backend:

- FastAPI
- SQLAlchemy
- Pydantic
- Alembic
- httpx
- python-dotenv
- psycopg
- redis if needed
- openai SDK or OpenAI-compatible lightweight client

Frontend:

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- lucide-react
- zod if needed

## 12. Non-goals for v0.1 Architecture

Avoid:

- Kubernetes
- enterprise multi-tenant RBAC
- full plugin marketplace
- complex event sourcing
- automatic code self-modification
- real destructive external actions

The architecture should be extensible, but v0.1 must stay buildable.

## 13. v0.2 Runtime Architecture

v0.2 keeps route handlers thin and moves behavior into services:

```text
Message API
  -> Task / Run records
  -> RunManager
      -> RunStateMachine
      -> MemoryRecallPipeline
      -> SkillSelector
      -> PromptBuilder
      -> Planner
      -> Executor
      -> ToolInvocationService
      -> ArtifactSpecBuilder / ArtifactValidator / ArtifactPersistenceService
      -> ConfirmationService
      -> MemoryCandidateExtractor
      -> ImprovementCandidateService
      -> RunMetricsRecorder
```

The runtime is still synchronous in v0.2, but state transitions, trace events, persisted tool invocations, metrics, and evals prepare the codebase for resumable workers.
