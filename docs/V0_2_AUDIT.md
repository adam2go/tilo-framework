# Tilo Framework v0.2 Audit

Date: 2026-04-25

## Scope

This audit starts Milestone 0 from `docs/V0_2_CODEX_PLAN.md`.

The highest-priority project constraints for all follow-up work are:

1. `AGENTS.md`
2. `docs/PROJECT_CONSTITUTION.md`
3. `docs/V0_2_CODEX_PLAN.md`
4. `docs/IMPLEMENTATION_RULES.md`
5. Domain docs for memory, artifacts, skills, API contracts, and security

The v0.2 implementation must preserve this loop:

Conversation -> Task -> Run -> Memory Recall -> Skill Selection -> Tool Execution -> Artifact Generation -> Human Confirmation -> Memory Update

Tilo must remain an AI-native SaaS agent framework, not a chatbot wrapper.

## Current Implementation Snapshot

### Backend

Current backend shape:

- FastAPI application entrypoint: `backend/app/main.py`
- Database/session setup: `backend/app/core/database.py`
- Settings: `backend/app/core/config.py`
- SQLAlchemy domain models: `backend/app/models/domain.py`
- Pydantic API schemas: `backend/app/schemas/domain.py`
- API routes:
  - `backend/app/api/routes/system.py`
  - `backend/app/api/routes/workspaces.py`
  - `backend/app/api/routes/projects.py`
  - `backend/app/api/routes/agents.py`
  - `backend/app/api/routes/tasks.py`
  - `backend/app/api/routes/runs.py`
  - `backend/app/api/routes/messages.py`
  - `backend/app/api/routes/memories.py`
  - `backend/app/api/routes/artifacts.py`
  - `backend/app/api/routes/confirmations.py`
  - `backend/app/api/routes/skills.py`
  - `backend/app/api/routes/tools.py`
- Runtime services:
  - `backend/app/services/agent_runtime/run_manager.py`
  - `backend/app/services/agent_runtime/planner.py`
  - `backend/app/services/agent_runtime/executor.py`
  - `backend/app/services/agent_runtime/prompt_builder.py`
  - `backend/app/services/memory/recall.py`
  - `backend/app/services/memory/extraction.py`
  - `backend/app/services/skill/selector.py`
  - `backend/app/services/tools/registry.py`
  - `backend/app/services/tools/invocation.py`
  - `backend/app/services/artifact/generator.py`
  - `backend/app/services/inbox/confirmations.py`
  - `backend/app/services/trace/recorder.py`
  - `backend/app/services/bootstrap.py`

Implemented v0.1 primitives:

- Workspace
- Project
- Agent
- Task
- Run
- TraceStep
- Artifact
- Confirmation
- Memory
- Skill
- Tool

The current `POST /api/messages` path creates a task, starts a run, recalls memory, selects a skill, executes a tool, generates an artifact, creates a pending confirmation, and extracts a memory candidate. This is aligned with the required product loop at a scaffold level.

### Frontend

Current frontend shape:

- Next.js app routes:
  - `frontend/app/page.tsx`
  - `frontend/app/workspaces/page.tsx`
  - `frontend/app/agents/page.tsx`
  - `frontend/app/inbox/page.tsx`
  - `frontend/app/memories/page.tsx`
  - `frontend/app/skills/page.tsx`
  - `frontend/app/projects/[id]/page.tsx`
  - `frontend/app/artifacts/[id]/page.tsx`
- Shared components:
  - `frontend/components/AppShell.tsx`
  - `frontend/components/Console.tsx`
  - `frontend/components/ArtifactRenderer.tsx`
  - `frontend/components/ResourcePages.tsx`
- Client helpers and types:
  - `frontend/lib/api.ts`
  - `frontend/lib/types.ts`

The frontend exposes a usable console and resource pages for framework primitives. It is currently a lightweight v0.1 UI rather than a complete v0.2 work surface.

## Local Startup Status

Current Docker startup path:

```bash
docker compose up --build -d
```

Verified locally:

- Backend health: `GET http://localhost:8000/api/health` returns `{"status":"ok"}`
- Frontend: `GET http://localhost:3000` returns HTTP 200
- Bootstrap: `GET http://localhost:8000/api/bootstrap` returns workspace, project, and agent data
- Demo loop: `POST http://localhost:8000/api/messages` creates a completed run with artifact, trace steps, pending confirmation, and memory candidate

Startup fixes currently present in the working tree:

- `docker-compose.yml` waits for Postgres health before starting the backend
- `frontend/next.config.mjs` no longer uses standalone output for the local Docker runtime
- `backend/app/api/routes/system.py` declares the bootstrap response model
- `backend/app/schemas/domain.py` defines `BootstrapResponse`

These fixes should be kept unless replaced by a cleaner equivalent.

## Test Status

There were no committed smoke tests before Milestone 0.

Added local smoke test:

- `backend/tests/test_smoke.py`

The smoke test covers:

- `GET /api/health`
- Bootstrap data
- `POST /api/messages`
- Artifact creation
- Trace creation
- Pending confirmation creation
- Unconfirmed memory candidate creation

Current limitation:

- Running `python3 -m pytest backend/tests/test_smoke.py` in the host environment fails because the local Python environment is missing project dependencies, starting with `pydantic_settings`.
- The Docker-based application path is verified and working.

## Implementation Gaps Against v0.2

### Long-Term Memory

Current memory implementation is too shallow for v0.2:

- Recall is primarily simple keyword/context matching.
- There is no dedicated `MemoryRecallPipeline`.
- Recall does not yet log detailed scoring inputs and decisions.
- Memory candidate lifecycle is not explicit enough.
- Memory records do not fully model event history, salience, source, scope, or confirmation/edit/delete workflows expected by the docs.
- Memory inspection/edit/delete UI is basic.

Required direction:

- Add structured recall pipeline with deterministic filters and scoring.
- Add durable recall trace data.
- Add memory event/candidate lifecycle support.
- Keep memory confirmable, inspectable, editable, and deletable.

### Artifact Delivery

Current artifact implementation is scaffold-level:

- Artifact generation is service-backed, but artifact schemas are hardcoded and not yet centered on `artifact_spec.v1`.
- There is no robust schema validation layer for generated artifacts.
- Renderer selection is simple and not registry-driven.
- Artifact detail page exists but is not yet a full AI-native result delivery experience.
- Artifacts are not yet versioned or rich enough for the v0.2 result contract.

Required direction:

- Introduce `artifact_spec.v1`.
- Refactor artifact generation around schema-driven output.
- Add backend validation and frontend renderer registry.
- Add artifact evals for required fields and renderer compatibility.

### Safe Agent Self-Improvement

The current implementation does not yet support the v0.2 self-improvement loop:

- No agent feedback model/API.
- No agent run metrics aggregation.
- No skill improvement candidate model.
- No approval workflow for proposed skill/prompt/tool policy changes.
- No durable audit trail for self-improvement decisions.

Required direction:

- Add feedback collection connected to artifacts/runs.
- Add agent run metrics.
- Add skill improvement candidates requiring human approval.
- Ensure no automatic self-modification without durable confirmation.

### Tools And Confirmations

Current tool and confirmation support is present but minimal:

- Tool execution is represented, but invocation records are not yet rich enough as a durable ledger.
- High-risk tool policy needs stronger enforcement.
- Confirmation records exist, but v0.2 needs stricter linkage to risky actions, artifacts, and memory updates.

Required direction:

- Add a durable tool invocation ledger.
- Enforce confirmation requirements before high-risk side effects.
- Link confirmations to the exact proposed operation and target record.

### Run Management

Current run execution works for the demo loop but needs hardening:

- Run state transitions are simple.
- Error handling is not yet complete enough for production traces.
- There is no explicit retry/cancellation model.
- Trace steps exist, but v0.2 needs more complete observability around memory recall, skill selection, tool execution, artifact validation, and confirmation creation.

Required direction:

- Harden `RunManager` state transitions.
- Record failures as structured trace steps.
- Keep route handlers thin and push business logic into services.

### API Contracts

The existing API surface is useful for v0.1 but incomplete for v0.2:

- Memory candidate lifecycle endpoints need expansion.
- Artifact spec/version endpoints need refinement.
- Feedback and self-improvement endpoints are missing.
- Tool invocation ledger endpoints are missing.
- Some route handlers may need additional service extraction as the implementation grows.

Required direction:

- Keep API schemas explicit with Pydantic v2.
- Add v0.2 APIs in service-backed slices.
- Avoid leaking implementation-specific payloads as public contracts.

### Frontend

Current UI is functional but not complete for v0.2:

- Memory workbench is basic.
- Artifact renderer is not registry-driven.
- Confirmation inbox is basic.
- There is no self-improvement review surface.
- Some components live in broad shared files and may need more focused module boundaries as v0.2 grows.

Required direction:

- Build real framework surfaces around memory, artifacts, confirmations, feedback, and skills.
- Do not add disconnected mock pages.
- Keep pages connected to real Task, Run, TraceStep, Artifact, Confirmation, Memory, Skill, and Tool data.

## Refactor Risks

Primary risks before feature work:

1. Data model evolution may require migrations or careful schema creation rules.
2. Memory changes can easily break the core demo loop if recall/extraction contracts drift.
3. Artifact schema changes can break both API responses and frontend renderers.
4. Confirmation enforcement can deadlock the demo loop if all actions are treated as high-risk.
5. Docker startup depends on service readiness and frontend build output assumptions.
6. Host-based tests currently require dependency installation; Docker verification remains the reliable path until the local test environment is prepared.

## Milestone 0 Result

Milestone 0 status:

- Required docs were read.
- Current backend/frontend implementation was inspected.
- Local Docker startup was verified.
- Current v0.1 demo loop was verified.
- A backend smoke test was added, but host execution is blocked by missing local dependencies.
- This audit document was created.

## Next 5 Development Tasks

1. Implement `MemoryRecallPipeline` with deterministic filtering, structured scoring, and trace logging.
2. Add memory candidate lifecycle models/services/endpoints for confirm, edit, reject, and delete.
3. Introduce `artifact_spec.v1` and refactor artifact generation around schema validation.
4. Add frontend artifact renderer registry and improve the artifact detail surface using real artifact schemas.
5. Add feedback and safe self-improvement primitives: feedback records, run metrics, skill improvement candidates, and approval-gated application.
