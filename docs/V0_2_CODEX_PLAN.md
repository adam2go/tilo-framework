# Tilo Framework v0.2 Codex Implementation Plan

This document is the execution plan for Tilo Framework v0.2.

It is written for Codex, Claude Code, and human contributors. Before implementing v0.2, read this file together with:

1. `AGENTS.md`
2. `docs/PROJECT_CONSTITUTION.md`
3. `docs/PRODUCT_PRINCIPLES.md`
4. `docs/CODEX_SPEC.md`
5. `docs/ARCHITECTURE.md`
6. `docs/IMPLEMENTATION_RULES.md`
7. `docs/QUALITY_BAR.md`
8. `docs/MEMORY.md`
9. `docs/ARTIFACTS.md`
10. `docs/SKILLS.md`
11. `docs/UI_UX.md`
12. `docs/SECURITY.md`
13. `docs/DATA_PRIVACY.md`
14. `docs/DEVELOPMENT_WORKFLOW.md`

If anything conflicts, follow this priority:

```text
PROJECT_CONSTITUTION.md > AGENTS.md > this v0.2 plan > module docs > local implementation convenience
```

---

## 1. v0.2 Product Goal

Tilo v0.1 proves the basic loop:

```text
Conversation -> Task -> Run -> Memory Recall -> Skill Selection -> Tool Execution -> Artifact Generation -> Human Confirmation -> Memory Candidate
```

Tilo v0.2 must make this loop meaningfully stronger in three areas:

1. **Long-term memory**  
   Move from simple keyword recall to a structured memory system with candidate governance, recall logging, scope-aware retrieval, and future-ready embedding/rerank support.

2. **Agent self-improvement**  
   Move from passive memory extraction to an explicit improvement loop: run ledger, feedback, skill candidates, evaluation gates, and safe promotion rules.

3. **AI-native artifact delivery**  
   Move from hardcoded artifact schemas to a real artifact protocol and renderer registry, so agent outputs can become durable, interactive, SaaS-like result pages.

v0.2 should still remain buildable. Do not attempt to build a full enterprise platform yet.

---

## 2. Current Implementation Audit Summary

The current implementation already has the right skeleton:

- Core domain models exist.
- `RunManager` executes a complete lightweight loop.
- Memory recall exists.
- Artifact generation exists.
- Confirmation generation exists.
- Trace recording exists.
- Docs and project constraints are strong.

However, current implementation is still v0.1-level:

### 2.1 Memory is too shallow

Current memory recall is keyword-overlap based. It does not yet support:

- semantic embedding search
- hybrid ranking
- recency/salience weighting
- memory candidate lifecycle beyond simple `is_confirmed`
- memory write event logs
- recall event logs
- memory conflict detection
- memory supersession/versioning
- project/user/workspace scope ranking

### 2.2 Artifact generation is too hardcoded

Current artifact generation is mostly keyword detection plus hardcoded schema generation. It does not yet support:

- a formal `artifact_spec.v1`
- schema validation
- renderer registry
- artifact actions linked to durable confirmations
- artifact provenance
- artifact versioning beyond a numeric version field
- artifact patching or progressive updates
- standalone result page quality

### 2.3 Self-improvement is under-specified in code

Current system can extract memory candidates, but does not yet support:

- explicit feedback records
- run outcome scoring
- skill candidate generation
- skill promotion workflow
- evaluation-driven improvement
- rollback for bad skill/memory changes

### 2.4 Runtime is synchronous and linear

Current `RunManager` executes everything in one synchronous flow. This is acceptable for v0.1, but v0.2 should prepare for:

- resumable runs
- structured run state transitions
- trace-safe event logging
- future async workers
- partial artifact updates

### 2.5 Eval and benchmark system is missing

There is no strong evidence loop yet to prove Tilo is better than other frameworks.

v0.2 needs at least lightweight benchmark scaffolding for:

- memory recall quality
- artifact schema validity
- run success rate
- confirmation flow correctness
- skill improvement safety

---

## 3. v0.2 Non-negotiables

Codex must preserve these rules:

1. Do not turn Tilo into a chatbot wrapper.
2. Do not bypass Task, Run, TraceStep, Artifact, Confirmation, Memory.
3. Do not store long-term memory as raw chat history only.
4. Do not generate only Markdown when a structured artifact is expected.
5. Do not let self-improvement automatically modify shared skills or system prompts without review.
6. Do not expose hidden chain-of-thought.
7. Do not log secrets.
8. Do not execute high-risk tools without durable confirmation.
9. Do not build disconnected demo pages.
10. Do not overbuild enterprise complexity before the v0.2 loop works.

---

## 4. Target v0.2 Architecture

v0.2 should evolve the runtime into this shape:

```text
Message API
  -> TaskService
  -> RunManager
      -> RunStateMachine
      -> MemoryRecallPipeline
      -> SkillSelector
      -> PromptBuilder
      -> Planner
      -> Executor
      -> ToolRegistry
      -> ArtifactSpecBuilder
      -> ConfirmationService
      -> MemoryCandidateExtractor
      -> ImprovementCandidateService
      -> RunMetricsRecorder
```

v0.2 should not necessarily implement every future capability fully, but it should create the right seams.

---

## 5. v0.2 Milestones

Implement in this order.

### Milestone 0: Stabilize and audit current code

Goal: understand current implementation and avoid breaking v0.1 loop.

Tasks:

1. Read all docs listed at the top of this file.
2. Inspect current backend and frontend structure.
3. Produce a short implementation audit in `docs/V0_2_AUDIT.md`.
4. Confirm current local startup commands.
5. Confirm existing tests or create smoke tests if none exist.

Acceptance:

- `docs/V0_2_AUDIT.md` exists.
- It lists current files, current behavior, known gaps, and v0.2 refactor risks.
- Current v0.1 demo loop still works.

Do not skip this milestone.

---

### Milestone 1: Memory v0.2 foundation

Goal: make memory structured, inspectable, loggable, and ready for better retrieval.

#### 1.1 Refactor memory model without breaking v0.1

Current `Memory` can remain, but extend it carefully.

Add fields if they do not exist:

```text
scope_type: user | workspace | project | skill | run
scope_id: string nullable
salience: float default 0.5
status: candidate | confirmed | rejected | archived
source_run_id: string nullable
supersedes_id: string nullable
structured_payload: JSON nullable
last_recalled_at: datetime nullable
recall_count: int default 0
```

If direct schema migration is not ready, add new models while preserving old `Memory` fields.

Recommended new models:

```text
MemoryWriteEvent
MemoryRecallEvent
MemoryConflict
```

#### 1.2 Add MemoryWriteEvent

Purpose: every memory write or candidate extraction should be auditable.

Fields:

```text
id
workspace_id
project_id nullable
memory_id nullable
run_id nullable
event_type: candidate_created | confirmed | rejected | edited | archived | superseded
payload_json
created_at
```

#### 1.3 Add MemoryRecallEvent

Purpose: measure recall quality and debug why a memory was used.

Fields:

```text
id
workspace_id
project_id nullable
run_id
query_text
retrieved_memory_ids JSON
scores_json JSON
strategy
created_at
```

#### 1.4 Implement MemoryRecallPipeline

Replace or wrap current `MemoryRecallService` with a pipeline:

```text
1. Scope filter
2. Status filter: confirmed only by default
3. Candidate retrieval
4. Scoring
5. Reranking
6. Recall event logging
7. Return top-k memories with scores
```

For v0.2, implement hybrid scoring using available data:

```text
score = keyword_score * 0.45 + salience * 0.25 + recency_score * 0.20 + scope_score * 0.10
```

If embeddings are available, upgrade to:

```text
score = semantic_score * 0.50 + keyword_score * 0.20 + salience * 0.15 + recency_score * 0.10 + scope_score * 0.05
```

Do not block v0.2 on embeddings. Keep embedding optional.

#### 1.5 Add MemoryCandidate workflow

Either use `Memory.status = candidate` or create `MemoryCandidate` model.

Candidate records should include:

```text
content
suggested_type
confidence
reason
source_run_id
source_artifact_id nullable
status: pending | accepted | rejected | edited
```

Default must be `pending` or `candidate`, not confirmed.

#### 1.6 Memory frontend upgrades

Memory UI should show:

- confirmed memories
- pending candidates
- type
- scope
- salience
- confidence
- source run/artifact if available
- accept/edit/reject buttons

Acceptance for Milestone 1:

- Memory recall still works.
- Recall events are recorded.
- Memory candidates are not silently confirmed.
- User can accept/reject/edit candidates.
- Confirmed memories can be recalled in later runs.
- Memory UI clearly separates confirmed memories and candidates.

Files likely affected:

```text
backend/app/models/domain.py or new backend/app/models/memory.py
backend/app/services/memory/recall.py
backend/app/services/memory/extraction.py
backend/app/services/memory/writer.py
backend/app/api/routes/memories.py
frontend/components/memory/*
frontend/lib/types.ts
frontend/lib/api.ts
```

---

### Milestone 2: Artifact Spec v1 and renderer registry

Goal: make artifacts a real product output protocol, not hardcoded demo schema.

#### 2.1 Define artifact_spec.v1

Create shared backend/frontend schema definitions.

Backend Pydantic model suggestion:

```python
class ArtifactSpecV1(BaseModel):
    version: Literal["artifact_spec.v1"] = "artifact_spec.v1"
    artifact_type: str
    title: str
    status: Literal["draft", "streaming", "ready", "failed"] = "ready"
    blocks: list[ArtifactBlock]
    actions: list[ArtifactAction] = []
    provenance: list[ProvenanceRef] = []
    memory_refs: list[str] = []
    run_id: str | None = None
```

Frontend TypeScript type suggestion:

```ts
export type ArtifactSpecV1 = {
  version: "artifact_spec.v1";
  artifact_type: string;
  title: string;
  status: "draft" | "streaming" | "ready" | "failed";
  blocks: ArtifactBlock[];
  actions: ArtifactAction[];
  provenance: ProvenanceRef[];
  memory_refs: string[];
  run_id?: string;
};
```

#### 2.2 Define block types

Supported v0.2 block types:

```text
markdown
rich_text
table
metric
card
list
timeline
kanban
risk_item
citation
form
comparison_matrix
```

Each block must have:

```text
id
type
title optional
data
```

#### 2.3 Define ArtifactAction

Artifact actions should be durable and confirmation-aware.

```ts
export type ArtifactAction = {
  id: string;
  label: string;
  action_type: "confirm" | "edit" | "regenerate" | "export" | "continue_task";
  confirmation_required: boolean;
  payload?: Record<string, unknown>;
};
```

If `confirmation_required=true`, backend should create or link a `Confirmation` record.

#### 2.4 Refactor ArtifactGenerator

Current generator should be split into:

```text
ArtifactTypeDetector
ArtifactSpecBuilder
ArtifactValidator
ArtifactPersistenceService
```

Do not keep all artifact logic in one file long term.

#### 2.5 Add artifact validation

Before saving artifact schema:

- validate `version`
- validate `artifact_type`
- validate blocks
- validate actions
- reject invalid schema with clear error

#### 2.6 Frontend renderer registry

Create a registry like:

```ts
const blockRenderers = {
  markdown: MarkdownBlock,
  table: TableBlock,
  metric: MetricBlock,
  card: CardBlock,
  risk_item: RiskItemBlock,
};
```

`ArtifactRenderer` should dispatch by block type.

Do not hardcode all rendering inside a single giant component.

#### 2.7 Artifact result pages

Each artifact should have a durable page:

```text
/artifacts/[id]
```

The page should show:

- artifact title
- status
- blocks
- actions
- linked run
- linked memory refs
- provenance if available

Acceptance for Milestone 2:

- Artifact schemas include `version: artifact_spec.v1`.
- Invalid artifact schema is rejected or normalized.
- Frontend uses renderer registry.
- Contract review artifact is rendered through the generic renderer path.
- Artifact actions create or link confirmations.
- Artifact detail page works.

Files likely affected:

```text
backend/app/services/artifact/generator.py
backend/app/services/artifact/*
backend/app/schemas/artifact.py
backend/app/api/routes/artifacts.py
frontend/components/artifact/*
frontend/app/artifacts/[id]/*
frontend/lib/types.ts
frontend/lib/api.ts
```

---

### Milestone 3: Safe agent self-improvement loop

Goal: introduce self-improvement without unsafe self-modification.

#### 3.1 Add RunOutcome / RunMetrics

Create a model or JSON structure to record run quality.

Fields:

```text
id
run_id
workspace_id
success: bool
latency_ms
artifact_count
confirmation_count
memory_candidate_count
tool_call_count
error_count
user_feedback_score nullable
created_at
```

#### 3.2 Add Feedback model

User feedback is crucial for self-improvement.

Fields:

```text
id
workspace_id
project_id nullable
run_id nullable
artifact_id nullable
memory_id nullable
skill_id nullable
rating: int nullable
feedback_text nullable
feedback_type: useful | not_useful | incorrect | incomplete | unsafe | other
created_at
```

#### 3.3 Add SkillCandidate

Do not auto-update real skills.

Create a `SkillCandidate` model:

```text
id
workspace_id
project_id nullable
source_run_id
name
description
trigger_description
instructions_markdown
artifact_template_json nullable
status: pending_review | approved | rejected | promoted
eval_report_json nullable
created_at
updated_at
```

#### 3.4 Skill candidate generation rules

Generate skill candidates only when:

- task was completed successfully
- user approved or positively interacted with artifact
- repeated task pattern is detected, or explicit user request says "save this as a skill"

Do not generate skill candidates for every run.

#### 3.5 Skill promotion gate

A skill candidate can become a real Skill only if:

1. User approves it.
2. It passes basic schema validation.
3. It does not request high-risk tools without permission.
4. It has an optional eval report or manual verification note.

#### 3.6 Self-improvement UI

Add a simple Skills Review panel:

- pending skill candidates
- source run
- proposed instructions
- artifact template
- approve/reject/edit buttons

Acceptance for Milestone 3:

- Run metrics are recorded.
- User feedback can be stored.
- Skill candidates can be generated and reviewed.
- No skill candidate is automatically promoted.
- Approved skill candidates can become Skill records.
- Promotion is traceable.

Files likely affected:

```text
backend/app/models/domain.py or new skill/improvement models
backend/app/services/improvement/*
backend/app/services/skill/*
backend/app/api/routes/skills.py
backend/app/api/routes/feedback.py
frontend/components/skills/*
frontend/app/skills/*
```

---

### Milestone 4: Runtime state machine and trace hardening

Goal: make runs more reliable, observable, and future-ready.

#### 4.1 Define run states

Allowed Run statuses:

```text
queued
running
waiting_for_confirmation
completed
failed
cancelled
```

Allowed Task statuses:

```text
created
running
waiting_for_confirmation
completed
failed
cancelled
```

Do not use arbitrary string statuses outside these values.

#### 4.2 Add RunStateMachine

Create a small service:

```text
RunStateMachine.transition(run, new_status, reason)
```

It should validate allowed transitions.

Example:

```text
queued -> running
running -> waiting_for_confirmation
running -> completed
running -> failed
waiting_for_confirmation -> running
waiting_for_confirmation -> completed
```

#### 4.3 Trace hardening

TraceStep should never expose:

- hidden chain-of-thought
- secrets
- raw credentials
- unnecessary raw document content

Add a trace sanitizer.

#### 4.4 Event-style trace helper

Trace recording should support:

```text
record_started
record_completed
record_failed
```

This makes long-running traces easier later.

#### 4.5 Error handling in RunManager

Wrap execution steps with error handling.

If a step fails:

- record failed trace step
- set run.status = failed
- set task.status = failed
- store safe error message
- do not leave run stuck in running

Acceptance for Milestone 4:

- Invalid run status transitions are prevented.
- Failed runs are marked failed.
- Trace output is sanitized.
- Runtime no longer leaves tasks in running on errors.
- Existing v0.1 demo still works.

Files likely affected:

```text
backend/app/services/agent_runtime/run_manager.py
backend/app/services/agent_runtime/state_machine.py
backend/app/services/trace/recorder.py
backend/app/models/domain.py
```

---

### Milestone 5: Tool permission and confirmation gate v0.2

Goal: make tool execution safe by design.

#### 5.1 Tool invocation ledger

Create `ToolInvocation` model:

```text
id
workspace_id
run_id
tool_id nullable
tool_name
tool_type
permission_level
input_json
output_json nullable
status: pending_confirmation | running | completed | failed | rejected
confirmation_id nullable
started_at nullable
completed_at nullable
created_at
```

#### 5.2 High-risk tool gate

If tool.permission_level == high:

- do not execute immediately
- create Confirmation
- create ToolInvocation with pending_confirmation
- resume only after approval

For v0.2, resuming can be simple, but do not silently execute high-risk tools.

#### 5.3 Mock tools must be labeled

Any mock tool response should include:

```json
{"mock": true}
```

Do not present mock external data as real data.

Acceptance for Milestone 5:

- Tool invocations are persisted.
- High-risk tools require Confirmation.
- Mock tools are clearly marked.
- Tool calls are traceable.

Files likely affected:

```text
backend/app/services/tools/*
backend/app/services/agent_runtime/executor.py
backend/app/services/inbox/confirmations.py
backend/app/models/domain.py
backend/app/api/routes/tools.py
```

---

### Milestone 6: Evaluation and benchmark scaffolding

Goal: prove Tilo quality can improve over time.

Create an `evals/` directory.

Recommended structure:

```text
evals/
  README.md
  datasets/
    memory_recall_cases.jsonl
    artifact_schema_cases.jsonl
    contract_review_cases.jsonl
  runners/
    run_memory_recall_eval.py
    run_artifact_schema_eval.py
  reports/
```

#### 6.1 Memory recall eval

Dataset example:

```json
{
  "query": "Review this contract using my usual risk preference",
  "memories": [
    {"id": "m1", "content": "User prefers conservative contract risk review", "expected": true},
    {"id": "m2", "content": "User likes short video scripts", "expected": false}
  ],
  "expected_memory_ids": ["m1"]
}
```

Metrics:

```text
recall_hit_rate@5
precision@5
false_positive_rate
```

#### 6.2 Artifact schema eval

Checks:

- valid artifact spec
- valid block types
- valid actions
- renderable by frontend registry

Metrics:

```text
artifact_schema_valid_rate
unsupported_block_rate
render_success_rate
```

#### 6.3 Runtime loop eval

Checks:

- task created
- run created
- trace created
- artifact created
- confirmation created when expected
- memory candidate created

Metric:

```text
end_to_end_loop_success_rate
```

Acceptance for Milestone 6:

- `evals/` exists.
- At least memory recall and artifact schema eval runners exist.
- README explains how to run evals.
- Codex can run evals locally without external paid APIs.

---

### Milestone 7: Frontend productization for AI-native result delivery

Goal: make the UI feel like an AI-native SaaS console.

#### 7.1 Artifact detail page

Implement or improve:

```text
/artifacts/[id]
```

Show:

- artifact title
- status
- version
- blocks
- actions
- linked run
- linked task
- memory refs
- trace link

#### 7.2 Context panel

Context panel should include tabs:

```text
Memory | Trace | Skills | Files
```

v0.2 can implement Files as placeholder.

#### 7.3 Inbox page upgrade

Inbox should show:

- pending confirmations
- approved/rejected confirmations
- source task/run
- risk level if available
- approve/reject/edit actions

#### 7.4 Memory review panel

Separate:

- confirmed memories
- pending candidates
- rejected/archived memories if useful

#### 7.5 Skill review panel

Show pending skill candidates.

Acceptance for Milestone 7:

- User can navigate from task/run to artifact.
- User can see trace and memory context.
- User can approve confirmations in Inbox.
- User can accept/reject memory candidates.
- UI does not rely on raw JSON dumps for normal operation.

---

## 6. P0 Priority Tasks

These must be done first.

### P0-1: Add `docs/V0_2_AUDIT.md`

Purpose: capture current implementation status before refactor.

Acceptance:

- Lists backend structure.
- Lists frontend structure.
- Lists existing APIs.
- Lists current memory/artifact/runtime limitations.
- Lists risky refactor areas.

### P0-2: Implement MemoryRecallPipeline with recall logging

Acceptance:

- Scope-aware recall.
- Confirmed-only recall by default.
- Hybrid keyword/salience/recency scoring.
- MemoryRecallEvent created per run.
- Existing recall tests pass.

### P0-3: Add memory candidate lifecycle

Acceptance:

- Candidates are not confirmed automatically.
- User can accept/reject/edit.
- Accepted candidate becomes confirmed memory.
- Write events are logged.

### P0-4: Define `artifact_spec.v1`

Acceptance:

- Backend Pydantic schema exists.
- Frontend TypeScript type exists.
- ArtifactGenerator emits `version: artifact_spec.v1`.
- Invalid specs are rejected or normalized.

### P0-5: Refactor ArtifactGenerator into spec builder components

Acceptance:

- No single giant artifact generator.
- Detector, builder, validator, persistence are separated.
- Existing demo artifacts still work.

### P0-6: Add ArtifactRenderer registry

Acceptance:

- Block renderers are registered by block type.
- Unsupported blocks render safe fallback.
- Contract review uses generic renderer path.

### P0-7: Add basic evals

Acceptance:

- `evals/` exists.
- Memory recall eval runs.
- Artifact schema eval runs.
- README explains commands.

### P0-8: Harden RunManager error handling

Acceptance:

- Failed steps mark run failed.
- Trace records failure.
- Task does not remain running forever.
- Safe error message stored.

---

## 7. P1 Priority Tasks

Do after P0.

### P1-1: Add RunMetrics and Feedback

Purpose: enable self-improvement.

Acceptance:

- RunMetrics recorded after run.
- Feedback API exists.
- Feedback can attach to run/artifact/memory/skill.

### P1-2: Add SkillCandidate workflow

Acceptance:

- Candidate can be generated.
- Candidate can be approved/rejected.
- Approved candidate can become Skill.
- No automatic promotion.

### P1-3: Add ToolInvocation ledger

Acceptance:

- Tool calls persisted.
- Tool status tracked.
- Confirmation linked for high-risk tools.

### P1-4: Add RunStateMachine

Acceptance:

- Allowed transitions enforced.
- Invalid transitions return clear errors.
- Runtime uses state machine.

### P1-5: Improve artifact result pages

Acceptance:

- `/artifacts/[id]` is useful as a standalone result page.
- Shows linked run/task/trace/memory.

---

## 8. P2 Priority Tasks

Do after P0/P1.

### P2-1: Optional embedding recall

Implement embeddings only after basic recall events and evals exist.

Acceptance:

- Embedding generation is optional.
- No external API required for tests.
- Recall pipeline supports semantic score when embeddings exist.

### P2-2: Memory conflict detection

Acceptance:

- Detect likely conflict by type/scope/content similarity.
- Create MemoryConflict records.
- Do not auto-resolve conflicts.

### P2-3: Artifact patch stream placeholder

Acceptance:

- Data model supports artifact updates/versions.
- Frontend can refresh or apply simple patches.
- No need for full realtime collaboration yet.

### P2-4: Public artifact sharing design

Do not enable public sharing by default.

Acceptance:

- Design doc exists.
- Security/privacy implications documented.

---

## 9. v0.2 Data Model Additions

Codex should add models carefully. If migrations are not ready, create models and document migration steps.

Recommended additions:

```text
MemoryWriteEvent
MemoryRecallEvent
MemoryConflict
RunMetric
Feedback
SkillCandidate
ToolInvocation
ArtifactVersion optional
```

Do not delete existing data model fields without migration plan.

---

## 10. v0.2 API Additions

Add or extend APIs.

### Memory

```text
POST /api/memories/recall
GET /api/memories/candidates
POST /api/memories/{id}/confirm
POST /api/memories/{id}/reject
POST /api/memories/{id}/archive
GET /api/memories/recall-events?run_id=
```

### Artifacts

```text
GET /api/artifacts/{id}
PATCH /api/artifacts/{id}
GET /api/artifacts/{id}/versions
POST /api/artifacts/{id}/actions/{action_id}
```

### Feedback

```text
POST /api/feedback
GET /api/feedback?run_id=&artifact_id=
```

### Skill Candidates

```text
GET /api/skill-candidates?workspace_id=&status=
POST /api/skill-candidates
POST /api/skill-candidates/{id}/approve
POST /api/skill-candidates/{id}/reject
POST /api/skill-candidates/{id}/promote
```

### Metrics

```text
GET /api/runs/{id}/metrics
```

---

## 11. Performance Targets

v0.2 should aim for these local dev targets with mock tools and no external LLM calls:

```text
p50 task-to-artifact latency: < 800ms
p95 task-to-artifact latency: < 2000ms
memory recall for 1k memories: < 150ms keyword/hybrid local
artifact render time for 50 blocks: < 500ms frontend
```

If external LLM calls are used, separate model latency from framework latency.

Add timing fields where useful:

```text
run.started_at
run.completed_at
trace_step.started_at
trace_step.completed_at
run_metrics.latency_ms
```

---

## 12. Security Hardening Checklist

Before v0.2 is considered complete:

- [ ] Tool permission levels enforced.
- [ ] High-risk tool calls create Confirmation.
- [ ] Trace sanitizer exists.
- [ ] Secrets are not logged.
- [ ] Memory candidates are not auto-confirmed.
- [ ] Artifact actions that mutate state use confirmation if risky.
- [ ] External content is treated as untrusted.
- [ ] Mock tools are labeled as mock.
- [ ] No hidden chain-of-thought is stored or displayed.

---

## 13. Documentation Updates Required

Update docs as implementation changes:

```text
docs/MEMORY.md
docs/ARTIFACTS.md
docs/SKILLS.md
docs/API_CONTRACTS.md
docs/ARCHITECTURE.md
docs/SECURITY.md
README.md
```

Add new docs:

```text
docs/V0_2_AUDIT.md
docs/V0_2_RELEASE_NOTES.md
evals/README.md
```

---

## 14. v0.2 Acceptance Criteria

Tilo v0.2 is complete when:

1. Existing v0.1 loop still works.
2. Memory recall is scope-aware and logged.
3. Memory candidates have clear lifecycle: pending, accepted, rejected, archived.
4. Artifact spec uses `artifact_spec.v1`.
5. Artifact renderer is registry-based.
6. Artifact detail page is useful as a result page.
7. Run failures are handled safely.
8. Trace output is sanitized.
9. At least one run metric record is created per completed run.
10. Skill candidates can be created and reviewed.
11. High-risk tools are confirmation-gated.
12. Basic evals exist and run locally.
13. Frontend supports artifact, memory, trace, inbox views in a coherent workflow.
14. Docs are updated.
15. No core demo bypasses Task/Run/Trace/Artifact/Confirmation/Memory.

---

## 15. Suggested Codex Execution Prompt

Use this prompt when asking Codex to implement v0.2:

```text
You are working on Tilo Framework v0.2.

Before coding, read:
- AGENTS.md
- docs/PROJECT_CONSTITUTION.md
- docs/V0_2_CODEX_PLAN.md
- docs/IMPLEMENTATION_RULES.md
- docs/MEMORY.md
- docs/ARTIFACTS.md
- docs/SKILLS.md
- docs/API_CONTRACTS.md
- docs/SECURITY.md

Then implement v0.2 in milestone order.

Start with Milestone 0 and create docs/V0_2_AUDIT.md.

Do not skip directly to feature coding.

The highest-priority goals are:
1. Stronger long-term memory
2. Safe agent self-improvement
3. AI-native artifact result delivery

Preserve the core loop:
Conversation -> Task -> Run -> Memory Recall -> Skill Selection -> Tool Execution -> Artifact Generation -> Human Confirmation -> Memory Update

Do not turn Tilo into a chatbot wrapper.
```

---

## 16. Final Reminder

v0.2 should not try to be everything.

The goal is to make Tilo's three differentiators real:

```text
Long-term memory that improves over time
Agent self-improvement with safety gates
AI-native artifact pages that feel like lightweight SaaS outputs
```

If a change does not support one of these, it is probably not a v0.2 priority.
