# Tilo v0.9: Artifact Action Runtime Plan

v0.9 is the next implementation milestone after v0.8 demo reliability and open-source DX.

v0.8 made Tilo easier to run, validate, and trust as an open-source project. v0.9 should now return to the core product/runtime differentiator:

```text
Interactive artifacts should not be frontend-only UI.
Artifact actions should be first-class backend runtime events.
```

The goal is to turn artifact buttons, mini-surface actions, memory confirmations, tool previews, and follow-up actions into a reusable runtime capability.

---

## 1. Why v0.9

Tilo already supports many ROAM primitives:

```text
Render -> Observe -> Act -> Memorize
```

Current implementation has:

- `ArtifactSpecV1`
- `ArtifactAction`
- interaction components
- `UIInteractionEvent`
- conversation observation turns
- confirmation APIs
- memory candidate APIs
- optional ORID reflection

But action handling is still too scattered:

- frontend components record interactions directly;
- frontend components decide which backend endpoint to call;
- confirmation, memory, tool, and continue-task actions are not handled by one runtime service;
- artifact actions are not executed through a single backend contract;
- channel adapters cannot easily reuse the same action behavior;
- tests can verify pieces, but not the unified action lifecycle.

This makes Tilo look like a working demo, not yet a reusable agent-app runtime.

v0.9 should introduce a single server-side action execution path.

---

## 2. Product Principle

Keep the core principle:

```text
Agent by default. UI when necessary.
```

Add this v0.9 principle:

```text
Frontend renders intent. Backend owns action semantics.
```

Frontend components should not know how to approve a confirmation, confirm memory, invoke a tool, or continue a task. They should send an artifact action request and render the result.

---

## 3. v0.9 Goals

v0.9 has five goals:

1. Add a unified backend Artifact Action Runtime.
2. Make action execution durable, observable, and idempotent enough for local/demo use.
3. Refactor frontend interaction components to use the unified action endpoint.
4. Reuse the same action runtime from web demo and Telegram callbacks where possible.
5. Add tests that prove the full action lifecycle.

---

## 4. Target Runtime Flow

Target action flow:

```text
User clicks artifact action
  -> POST /api/artifacts/{artifact_id}/actions/{action_id}
  -> ArtifactActionRuntime resolves action from artifact spec
  -> validate action + state binding + permission
  -> create UIInteractionEvent
  -> append ConversationTurn(observation) if session_id is available
  -> execute action handler
      - confirmation approve/reject
      - memory confirm/reject/create
      - continue task
      - invoke tool with confirmation gate
      - regenerate artifact
      - export placeholder
      - promote skill placeholder or existing skill flow
  -> optionally run ContextReflectionService
  -> return ActionResult
  -> frontend updates UI from result
```

The action runtime should become the shared contract for web, Telegram, and future channels.

---

## 5. P0: Add Action Execution API

### 5.1 Endpoint

Add:

```text
POST /api/artifacts/{artifact_id}/actions/{action_id}
```

Input:

```json
{
  "block_id": "risk_review_panel",
  "session_id": "optional-conversation-session-id",
  "run_id": "optional-run-id",
  "source": "web|telegram|api",
  "payload": {},
  "idempotency_key": "optional-client-generated-key"
}
```

Output:

```json
{
  "status": "completed|pending_confirmation|rejected|failed|noop",
  "action_id": "approve_revision",
  "artifact_id": "artifact-id",
  "block_id": "block-id",
  "interaction_event_id": "event-id",
  "conversation_turn_id": "turn-id-or-null",
  "confirmation_id": "confirmation-id-or-null",
  "memory_id": "memory-id-or-null",
  "tool_invocation_id": "tool-invocation-id-or-null",
  "task_id": "task-id-or-null",
  "run_id": "run-id-or-null",
  "artifact_version_id": "artifact-version-id-or-null",
  "message": "Human readable result summary",
  "next_actions": [],
  "warnings": []
}
```

### 5.2 Acceptance criteria

- Endpoint can execute an action defined at artifact-level or block-level.
- Unknown action returns 404 or 422 with a clear message.
- Unsupported action type returns safe `failed` or `noop`, not a 500.
- If `session_id` is provided, the action creates a linked observation turn.
- Existing direct endpoints remain backward compatible.

---

## 6. P0: ArtifactActionRuntime Service

Add service:

```text
backend/app/services/artifact/actions.py
```

Recommended classes:

```python
ArtifactActionRuntime
ArtifactActionResolver
ArtifactActionExecutor
ArtifactActionResult
```

### 6.1 Responsibilities

`ArtifactActionRuntime.execute(...)` should:

1. Load artifact.
2. Parse and validate `ArtifactSpecV1`.
3. Resolve action by `action_id` and optional `block_id`.
4. Validate state binding and permission intent.
5. Create `UIInteractionEvent`.
6. Append conversation observation turn when `session_id` exists.
7. Execute action by `action_type`.
8. Return structured `ArtifactActionResult`.

### 6.2 Action resolution rules

Action lookup order:

```text
1. If block_id is provided, search block.actions.
2. Search artifact.actions.
3. If action_id is not found, return 404/422.
```

If duplicate action ids exist across blocks, `block_id` is required.

### 6.3 Event type mapping

Use existing mapping, but move it server-side:

```text
approve / confirm -> artifact.action.approved
reject -> artifact.action.rejected
select -> artifact.option.selected
edit -> artifact.block.edited
create_memory -> memory.candidate.created
promote_skill -> skill.candidate.promoted
invoke_tool -> tool.invocation.requested
continue_task -> task.continue_requested
regenerate -> artifact.regenerate_requested
export -> artifact.export_requested
fallback -> artifact.action.clicked
```

### 6.4 Payload safety

Do not store secrets in event payloads.

Sanitize:

- API keys;
- tokens;
- authorization headers;
- passwords;
- full raw contract text when unnecessary;
- hidden reasoning.

Reuse existing sanitizer if available.

---

## 7. P0: Action Handlers

Implement small handler functions. Do not build a giant workflow engine.

### 7.1 Confirmation actions

For action types:

```text
approve
confirm
reject
```

Behavior:

- If `action.confirmation_id` exists, call existing confirmation approve/reject logic.
- If `state_binding.entity_type == confirmation`, use `state_binding.entity_id`.
- If confirmation is already decided, return `noop` with message.

### 7.2 Memory actions

For action types:

```text
create_memory
approve/confirm with memory binding
reject with memory binding
```

Behavior:

- Confirm memory when binding points to memory.
- Reject memory when binding points to memory.
- Create candidate memory for `create_memory`.
- Never create confirmed memory automatically.
- Return memory id in result.

### 7.3 Continue task actions

For action type:

```text
continue_task
```

Behavior:

- Requires `session_id` if it should continue the conversation.
- Uses conversation-native message path or shared message service.
- Appends user/system-style intent safely.
- Returns new task/run ids if created.

Example payload:

```json
{
  "content": "Generate a conservative revision draft for the approved risks."
}
```

### 7.4 Tool invocation actions

For action type:

```text
invoke_tool
```

Behavior:

- If tool is high-risk or action has `confirmation_required=true`, create or return pending confirmation.
- Do not silently execute high-risk tools.
- Low-risk deterministic tools may execute if existing tool service supports it.
- Return `pending_confirmation` when approval is needed.

### 7.5 Regenerate actions

For action type:

```text
regenerate
```

Behavior for v0.9:

- Minimal implementation is acceptable.
- It may create a new artifact version using existing deterministic generator, or return `noop` with a clear `coming soon` message.
- Do not fake a successful regeneration if no real path exists.

### 7.6 Export actions

For action type:

```text
export
```

Behavior for v0.9:

- Minimal implementation is acceptable.
- Return a clear message or simple JSON export payload.
- Do not claim PDF/DOCX export unless implemented.

### 7.7 Promote skill actions

For action type:

```text
promote_skill
```

Behavior:

- If skill candidate flow exists, call it.
- Otherwise return `noop` / `coming soon` clearly.

---

## 8. P0: Optional Action Execution Ledger

If implementation cost is reasonable, add model:

```text
ArtifactActionExecution
```

Suggested fields:

```text
id
workspace_id
project_id nullable
artifact_id
block_id nullable
action_id
action_type
session_id nullable
run_id nullable
interaction_event_id nullable
conversation_turn_id nullable
status
result_json
idempotency_key nullable
created_at
completed_at nullable
```

This is useful for debugging and idempotency.

If this is too much for v0.9, do not block the release. At minimum, `UIInteractionEvent` plus conversation observation turn must exist.

---

## 9. P1: Refactor Frontend Interaction Components

Current frontend components call multiple backend APIs directly. v0.9 should simplify them.

### 9.1 New frontend helper

Add:

```text
frontend/lib/artifactActions.ts
```

Or add to existing API client:

```ts
executeArtifactAction({ artifactId, blockId, actionId, sessionId, payload })
```

### 9.2 Component behavior

Components should:

1. Render action buttons from artifact schema.
2. Call unified action endpoint.
3. Show loading / success / failed / pending_confirmation state from `ActionResult`.
4. Avoid directly calling `/api/confirmations`, `/api/memories`, `/api/tools` unless as a documented fallback.

### 9.3 Acceptance criteria

- ApprovalCard uses unified action runtime.
- MemoryCandidateCard uses unified action runtime.
- RiskReviewPanel risk-level buttons use unified action runtime or produce valid server-side action requests.
- ActionQueue uses unified action runtime.
- Frontend no longer duplicates action semantics that belong to backend.

---

## 10. P1: Web Demo Integration

Update `/demo/telegram` carefully.

Required behavior:

- Pass `session_id` into artifact action execution.
- After action execution, refresh conversation turns or append returned result locally.
- Inspector should show action result, not only raw event.
- Approval path should still move demo stage forward.
- Memory confirmation should still show updated state.

Do not redesign the demo UI.

---

## 11. P1: Telegram Callback Integration

Telegram callbacks should reuse Artifact Action Runtime when callback maps to an artifact action.

Minimal path:

```text
Telegram callback
  -> resolve session
  -> resolve artifact/action from callback payload or short id
  -> ArtifactActionRuntime.execute(... source=telegram ...)
  -> send concise Telegram response
```

If callback does not include artifact/action context, preserve existing behavior.

Acceptance criteria:

- Existing Telegram callback tests still pass.
- Artifact-action callbacks can create UIInteractionEvent and observation turn.
- High-risk actions are not silently executed.

---

## 12. P1: Context Reflection Hook

After action execution, optionally run `ContextReflectionService` when:

- action is approve/confirm/reject/select/edit;
- session_id is available;
- action payload suggests reusable preference.

Rules:

- Reflection may create memory candidates.
- Reflection must not auto-confirm memory.
- Reflection errors should not break action execution; add warning to ActionResult.

---

## 13. P1: Documentation Updates

Add:

```text
docs/ARTIFACT_ACTION_RUNTIME.md
```

Explain:

- why backend owns action semantics;
- endpoint shape;
- action types;
- ActionResult shape;
- how frontend components should use it;
- how channel adapters should use it;
- safety and confirmation rules.

Update:

```text
docs/ARTIFACTS.md
docs/API_CONTRACTS.md
docs/CONVERSATION_RUNTIME.md
docs/BUILD_YOUR_FIRST_TILO_APP.md
docs/README.md
```

---

## 14. P2: Evals / Verification

Add a lightweight eval or verification script if useful:

```text
evals/runners/run_artifact_action_runtime_eval.py
```

Checks:

- action resolves;
- interaction event created;
- observation turn created;
- confirmation/memory side effect works;
- unsupported action fails safely.

Do not block v0.9 on a large eval framework.

---

## 15. Testing Requirements

Required backend tests:

1. `POST /api/artifacts/{id}/actions/{action_id}` resolves artifact-level action.
2. Resolves block-level action when `block_id` is provided.
3. Duplicate block action ids require `block_id`.
4. Unknown action returns clear error.
5. Approve action with confirmation id approves confirmation.
6. Reject action with confirmation id rejects confirmation.
7. Confirm memory action confirms memory candidate.
8. Reject memory action rejects memory candidate.
9. Create memory action creates unconfirmed candidate only.
10. Action with `session_id` creates `UIInteractionEvent` and `ConversationTurn(observation)`.
11. Continue task action creates or reuses conversation-native message flow.
12. Invoke high-risk tool action returns `pending_confirmation`.
13. Unsupported action type returns safe failure/noop.
14. Action payload sanitizer removes obvious secrets.
15. Existing demo/runtime tests still pass.

Required frontend checks if available:

- frontend build passes;
- interaction components compile with new helper;
- no direct runtime-only imports from backend assumptions.

---

## 16. Non-goals

Do not do these in v0.9:

- full workflow engine;
- full artifact editor;
- production-grade idempotency system;
- complete tool marketplace;
- full export to PDF/DOCX unless already easy;
- new app scenarios;
- major UI redesign;
- advanced permission system beyond current confirmation gate.

---

## 17. Definition of Done

v0.9 is complete when:

1. Artifact actions can be executed through one backend endpoint.
2. Action runtime creates `UIInteractionEvent` for important actions.
3. Action runtime appends conversation observation turn when `session_id` is provided.
4. Confirmation and memory actions work through the unified runtime.
5. High-risk or confirmation-required tool actions are gated.
6. Frontend interaction components use the unified action endpoint.
7. `/demo/telegram` still works and passes session id into action execution.
8. Telegram callback path can reuse action runtime where action context exists.
9. Docs explain Artifact Action Runtime clearly.
10. Tests cover the action lifecycle and existing v0.8 reliability checks still pass.
