# ROAM Codex Implementation Plan

This document is the implementation plan for making ROAM Loop the core product and architecture direction of Tilo.

ROAM stands for:

```text
Render -> Observe -> Act -> Memorize
```

Before implementing this plan, Codex must read:

1. `AGENTS.md`
2. `docs/PROJECT_CONSTITUTION.md`
3. `docs/PRODUCT_PRINCIPLES.md`
4. `docs/ROAM_LOOP.md`
5. `docs/AI_NATIVE_INTERACTION_COMPONENTS.md`
6. `docs/ARTIFACTS.md`
7. `docs/MEMORY.md`
8. `docs/API_CONTRACTS.md`
9. `docs/SECURITY.md`
10. `docs/UI_UX.md`

---

## 1. Goal

The goal is not to make the current UI prettier.

The goal is to make Tilo a ROAM-native AI SaaS agent framework where:

```text
Agent renders interactive UI
User interaction becomes structured observation
Agent acts on those observations
Confirmed learning becomes memory
```

This should become visible in code, docs, API, frontend components, and demos.

---

## 2. Non-negotiable Direction

Do not implement Tilo as:

- a chatbot wrapper
- a static artifact viewer
- a generic admin dashboard
- a local-only frontend state demo
- a hardcoded demo page

Tilo must be implemented as:

```text
Conversation-driven command center + agent-generated interaction surface + durable observation/memory loop
```

---

## 3. Target ROAM Flow

A complete ROAM-compatible run should look like this:

```text
1. User enters goal in conversation surface.
2. Backend creates Task and Run.
3. Agent renders Artifact with interaction components.
4. User interacts with Artifact components.
5. Frontend sends interaction event to backend.
6. Backend stores UIInteractionEvent / Confirmation / Feedback / MemoryCandidate.
7. Agent acts based on durable observation.
8. Artifact updates or follow-up task starts.
9. Memory candidates are generated.
10. User confirms memory.
11. Confirmed memory is recalled in future runs.
```

---

## 4. Phase 1: Documentation and README alignment

Already started. Verify these docs exist and are linked:

- `docs/ROAM_LOOP.md`
- `docs/AI_NATIVE_INTERACTION_COMPONENTS.md`
- `docs/ROAM_CODEX_IMPLEMENTATION_PLAN.md`
- `README.md`
- `README.zh-CN.md`
- `docs/PRODUCT_PRINCIPLES.md`

Acceptance:

- README explains ROAM Loop.
- Chinese README explains ROAM Loop.
- Product principles define ROAM as core product spine.
- Documentation links are not broken.

---

## 5. Phase 2: Add ROAM data primitives

### 5.1 Add UIInteractionEvent model

Add a durable model for UI observations.

Recommended fields:

```text
id
workspace_id
project_id nullable
user_id nullable
artifact_id nullable
block_id nullable
action_id nullable
run_id nullable
event_type
payload_json
created_at
```

Recommended event types:

```text
artifact.action.clicked
artifact.action.approved
artifact.action.rejected
artifact.block.edited
artifact.option.selected
memory.candidate.confirmed
memory.candidate.rejected
skill.candidate.promoted
tool.invocation.approved
feedback.submitted
```

### 5.2 Add API endpoints

Add endpoints:

```text
POST /api/interactions
GET /api/interactions?workspace_id=&artifact_id=&run_id=
```

The POST endpoint should accept:

```json
{
  "workspace_id": "string",
  "project_id": "string|null",
  "artifact_id": "string|null",
  "block_id": "string|null",
  "action_id": "string|null",
  "run_id": "string|null",
  "event_type": "artifact.action.clicked",
  "payload": {}
}
```

Acceptance:

- UI interaction is persisted.
- Interaction events can be queried.
- Events do not store secrets.
- Events can be linked to Artifact/Run/Memory/Confirmation where applicable.

Likely files:

```text
backend/app/models/domain.py or backend/app/models/interactions.py
backend/app/schemas/interactions.py
backend/app/api/routes/interactions.py
backend/app/services/interactions/*
frontend/lib/api.ts
frontend/lib/types.ts
```

---

## 6. Phase 3: Extend Artifact schema for ROAM

### 6.1 Extend ArtifactBlock

Artifact blocks should support:

```ts
export type ArtifactBlock = {
  id: string;
  type: string;
  title?: string;
  data: Record<string, unknown>;
  actions?: ArtifactAction[];
  state_binding?: StateBinding;
};
```

### 6.2 Extend ArtifactAction

```ts
export type ArtifactAction = {
  id: string;
  label: string;
  action_type:
    | "approve"
    | "reject"
    | "edit"
    | "select"
    | "continue_task"
    | "regenerate"
    | "invoke_tool"
    | "create_memory"
    | "promote_skill"
    | "export";
  confirmation_required: boolean;
  payload?: Record<string, unknown>;
};
```

### 6.3 Add StateBinding

```ts
export type StateBinding = {
  entity_type:
    | "artifact"
    | "confirmation"
    | "memory"
    | "skill_candidate"
    | "tool_invocation"
    | "task"
    | "run";
  entity_id: string;
  field?: string;
};
```

Acceptance:

- Backend validates action and state binding fields.
- Frontend types include actions and state bindings.
- Existing artifact demos still render.
- Unknown actions/blocks fail gracefully.

---

## 7. Phase 4: Build interaction component registry

Create a frontend registry:

```text
frontend/components/interaction/registry.tsx
```

Initial components:

```text
ApprovalCard
RiskReviewPanel
ComparisonMatrix
MetricDashboard
MemoryCandidateCard
ToolCallPreview
ActionQueue
EditableDocumentPlaceholder
```

Each component should:

- receive block data
- render professional UI
- expose supported actions
- call backend APIs for durable state changes
- record UIInteractionEvent where appropriate

Do not keep all component rendering inside one giant ArtifactRenderer.

Acceptance:

- ArtifactRenderer dispatches interaction blocks through registry.
- At least 6 reusable interaction components exist.
- Components are not hardcoded to only one demo.
- Component actions create durable backend events.

---

## 8. Phase 5: Connect component actions to backend state

Component actions should map to real backend state.

| Component Action | Backend State |
|---|---|
| approve | Confirmation approved or interaction event |
| reject | Confirmation rejected or interaction event |
| edit | Artifact update or interaction event |
| select | UIInteractionEvent + optional Feedback |
| continue_task | Message API / Task API |
| invoke_tool | ToolInvocation + Confirmation if high-risk |
| create_memory | MemoryCandidate / Memory API |
| promote_skill | SkillCandidate API |

Acceptance:

- No important component action is local-only.
- Actions create UIInteractionEvent.
- Risky actions are confirmation-gated.
- Memory candidate confirmation still works.

---

## 9. Phase 6: Redesign Console around ROAM

The Console should make ROAM visible.

Recommended layout:

```text
Conversation / Goal Steering
  + Run Progress
  + Clarification / Next Steps

Generated Interaction Surface
  + Artifact pages
  + AI-native components

Context / Control
  + Trace
  + Memory
  + Skills
  + Inbox
```

Changes:

1. Make the conversation/task area feel like the command center.
2. Make the generated Artifact surface visually dominant.
3. Use interaction components in the artifact area.
4. Show pending confirmations and memory candidates clearly.
5. Add a visible ROAM progress strip:

```text
Render -> Observe -> Act -> Memorize
```

Acceptance:

- First-time user understands ROAM within 10 seconds.
- Demo prompts explain what component surface will be generated.
- UI no longer feels like a debug console.
- No raw JSON in normal user flow.

---

## 10. Phase 7: Showcase demos

Update demos to prove ROAM.

### Contract Review

Should show:

```text
RiskReviewPanel -> ApprovalCard -> EditableDocumentPlaceholder -> MemoryCandidateCard
```

### Sales Follow-up

Should show:

```text
MetricDashboard -> DecisionTable/ActionQueue -> ApprovalCard -> MemoryCandidateCard
```

### Competitive Analysis

Should show:

```text
ComparisonMatrix -> OptionPicker or Selection Action -> ContinueTaskInput -> MemoryCandidateCard
```

Acceptance:

- Each demo demonstrates Render, Observe, Act, and Memorize.
- Each demo includes at least one durable user interaction.
- Each demo looks good enough for README screenshots.

---

## 11. Phase 8: Tests and evals

Add tests or checks for:

- creating UIInteractionEvent
- artifact action schema validation
- component action API calls
- memory candidate confirmation event
- confirmation approval event
- artifact renderer fallback

Add eval note:

```text
ROAM demo success = artifact renders + user action persists + follow-up state changes + memory candidate created/confirmed
```

---

## 12. Anti-patterns

Do not:

- only update CSS
- only add static cards
- store component interactions only in React state
- generate UI with arbitrary unsafe HTML
- make every component demo-specific
- bypass Confirmation for high-risk actions
- turn memory confirmation into a fake button
- hide ROAM behind internal implementation details

---

## 13. Suggested Codex prompt

Use this prompt:

```text
Read these files first:
- docs/ROAM_LOOP.md
- docs/AI_NATIVE_INTERACTION_COMPONENTS.md
- docs/ROAM_CODEX_IMPLEMENTATION_PLAN.md
- docs/PRODUCT_PRINCIPLES.md
- docs/ARTIFACTS.md
- docs/API_CONTRACTS.md
- docs/SECURITY.md

Implement the ROAM Loop foundation.

Do not simply beautify the UI.

Focus on making UI interaction a first-class part of the agent loop:
Render -> Observe -> Act -> Memorize.

Implement in this order:
1. Add UIInteractionEvent model and API.
2. Extend ArtifactBlock/ArtifactAction with actions and state_binding.
3. Add frontend interaction component registry.
4. Implement ApprovalCard, RiskReviewPanel, ComparisonMatrix, MetricDashboard, MemoryCandidateCard, ToolCallPreview, ActionQueue.
5. Make component actions call backend APIs and persist UIInteractionEvent.
6. Redesign Console to make conversation + generated interaction surface the main experience.
7. Update demos to prove ROAM.
8. Add minimal tests.

Preserve existing APIs when possible.
Do not create local-only fake interactions.
Do not turn Tilo into a chatbot wrapper.
```

---

## 14. Definition of Done

ROAM foundation is done when:

1. README and product docs position Tilo around ROAM.
2. UIInteractionEvent exists and can be persisted.
3. Artifact actions and state bindings are supported.
4. Interaction component registry exists.
5. At least 6 interaction components render from artifact schema.
6. Component actions create durable backend observations.
7. Console visibly communicates Render -> Observe -> Act -> Memorize.
8. Demos prove at least one full ROAM path.
9. Memory confirmation remains durable.
10. High-risk actions remain confirmation-gated.
