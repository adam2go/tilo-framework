# Tilo v0.9 Codex Execution Prompt

Use this prompt when asking Codex to implement v0.9.

```text
We are continuing development of Tilo Framework v0.9.

Repository:
adam2go/tilo-framework

First read:
- README.md
- docs/README.md
- docs/V0_9_ARTIFACT_ACTION_RUNTIME_PLAN.md
- docs/ROAM_LOOP.md
- docs/ARTIFACTS.md
- docs/CONVERSATION_RUNTIME.md
- docs/ORID_CONTEXT_REFLECTION.md
- docs/MEMORY.md
- docs/API_CONTRACTS.md
- docs/QUALITY_BAR.md

Goal:
Implement v0.9: Artifact Action Runtime.

This is not a UI redesign and not a new demo feature.
The goal is to make artifact actions a reusable backend runtime capability.

Core principles:
- Frontend renders intent. Backend owns action semantics.
- Preserve ROAM: Render -> Observe -> Act -> Memorize.
- Preserve conversation-first UX.
- Preserve deterministic mode and optional LLM mode.
- Preserve existing /demo/telegram behavior.
- Do not add a new app category.
- Do not build a full workflow engine.
- Do not build a full artifact editor.
- Do not silently execute high-risk tools.
- Do not auto-confirm memory.
- Keep implementation small, reliable, and well-tested.

Background:
Current frontend interaction components record UIInteractionEvent and then directly call various backend APIs such as confirmations, memories, tools, and skills. That works for a demo, but it scatters action semantics across the frontend. v0.9 should move action semantics into one backend runtime path.

Target flow:
User clicks artifact action
-> POST /api/artifacts/{artifact_id}/actions/{action_id}
-> ArtifactActionRuntime resolves action from artifact spec
-> validates action, state binding, permission intent
-> creates UIInteractionEvent
-> appends ConversationTurn(observation) if session_id is available
-> executes confirmation/memory/tool/continue-task/regenerate/export handler
-> optionally runs ContextReflectionService
-> returns structured ActionResult
-> frontend renders ActionResult

Implement in this order:

1. Add backend action result schemas.
   - Add request/response schemas for artifact action execution.
   - Input fields:
     block_id optional,
     session_id optional,
     run_id optional,
     source default web,
     payload default {},
     idempotency_key optional.
   - Output fields:
     status,
     action_id,
     artifact_id,
     block_id,
     interaction_event_id nullable,
     conversation_turn_id nullable,
     confirmation_id nullable,
     memory_id nullable,
     tool_invocation_id nullable,
     task_id nullable,
     run_id nullable,
     artifact_version_id nullable,
     message,
     next_actions,
     warnings.

2. Add ArtifactActionRuntime service.
   - Create backend/app/services/artifact/actions.py.
   - Implement ArtifactActionRuntime.execute(...).
   - Load Artifact by id.
   - Parse and validate ArtifactSpecV1.
   - Resolve action by action_id and optional block_id.
   - Lookup order:
     a. if block_id provided, search that block.actions;
     b. search artifact.actions;
     c. if duplicate action ids across blocks exist and block_id is omitted, return clear error.
   - Validate action_type and state_binding.
   - Sanitize payload before persistence.
   - Create UIInteractionEvent for important actions.
   - If session_id is provided, append linked ConversationTurn(observation) via ConversationService.
   - Return ArtifactActionResult.

3. Add action execution API.
   - Add POST /api/artifacts/{artifact_id}/actions/{action_id}.
   - Keep existing artifact endpoints backward compatible.
   - Unknown action should return 404 or 422 with clear detail.
   - Unsupported action should return safe failed/noop ActionResult, not a 500.

4. Implement action handlers.

   Confirmation:
   - approve/confirm with confirmation_id approves confirmation.
   - reject with confirmation_id rejects confirmation.
   - state_binding.entity_type=confirmation should work.
   - Already decided confirmation returns noop.

   Memory:
   - approve/confirm with state_binding.entity_type=memory confirms memory candidate.
   - reject with memory binding rejects memory candidate.
   - create_memory creates candidate memory only, never confirmed.
   - Return memory_id.

   Continue task:
   - continue_task requires session_id for conversation continuation.
   - Use conversation-native message path or shared message service.
   - Return task_id/run_id if created.
   - If not enough data, return failed/noop with clear message.

   Tool invocation:
   - invoke_tool with confirmation_required=true or high-risk tool should return pending_confirmation.
   - Do not silently execute high-risk tools.
   - Low-risk tool execution can use existing tool service if available.
   - Return tool_invocation_id if available; otherwise return clear message.

   Regenerate:
   - Minimal implementation is acceptable.
   - If no real regenerate path exists, return noop with clear coming-soon message.
   - Do not fake a successful regeneration.

   Export:
   - Minimal implementation is acceptable.
   - Return simple JSON/export placeholder only if truthful.
   - Do not claim PDF/DOCX export unless implemented.

   Promote skill:
   - If skill candidate flow exists, use it.
   - Otherwise return noop/coming-soon clearly.

5. Optional but preferred: add ArtifactActionExecution ledger.
   - Add model only if it fits current schema/migration style.
   - Fields:
     id,
     workspace_id,
     project_id nullable,
     artifact_id,
     block_id nullable,
     action_id,
     action_type,
     session_id nullable,
     run_id nullable,
     interaction_event_id nullable,
     conversation_turn_id nullable,
     status,
     result_json,
     idempotency_key nullable,
     created_at,
     completed_at nullable.
   - If this is too much, do not block v0.9. UIInteractionEvent + observation turn are mandatory.

6. Refactor frontend interaction components.
   - Add frontend/lib/artifactActions.ts or equivalent helper.
   - Implement executeArtifactAction({ artifactId, blockId, actionId, sessionId, payload }).
   - Refactor ApprovalCard, MemoryCandidateCard, RiskReviewPanel, ActionQueue, ToolCallPreview where practical to call the unified endpoint.
   - Components should no longer decide how to approve confirmations or confirm memories directly, except as documented fallback.
   - Show ActionResult status:
     completed,
     pending_confirmation,
     rejected,
     failed,
     noop.

7. Update /demo/telegram integration.
   - Pass session_id into action execution when available.
   - Keep optimistic UI but reconcile with ActionResult.
   - Approval path should still move demo stage forward.
   - Memory path should still show updated state.
   - Inspector should show action result or action event where useful.
   - Do not redesign the demo.

8. Update Telegram callback integration.
   - If callback payload can resolve artifact_id/action_id/block_id, call ArtifactActionRuntime.
   - If callback lacks artifact action context, preserve existing callback behavior.
   - Existing Telegram tests should still pass.
   - High-risk actions must remain gated.

9. Add optional ContextReflection hook.
   - After successful approve/confirm/reject/select/edit, if session_id exists, optionally run ContextReflectionService.
   - Reflection may create memory candidates.
   - Reflection errors must not break action execution; add warning to ActionResult.
   - Do not auto-confirm memory.

10. Add docs.
   - Add docs/ARTIFACT_ACTION_RUNTIME.md.
   - Explain endpoint shape, ActionResult, supported action types, safety rules, frontend usage, and channel adapter usage.
   - Update docs/ARTIFACTS.md.
   - Update docs/API_CONTRACTS.md.
   - Update docs/CONVERSATION_RUNTIME.md.
   - Update docs/BUILD_YOUR_FIRST_TILO_APP.md.
   - Update docs/README.md to link ARTIFACT_ACTION_RUNTIME.md.

11. Add tests.

Required backend tests:
- POST /api/artifacts/{id}/actions/{action_id} resolves artifact-level action.
- Resolves block-level action when block_id is provided.
- Duplicate block action ids require block_id.
- Unknown action returns clear error.
- Approve action with confirmation id approves confirmation.
- Reject action with confirmation id rejects confirmation.
- Confirm memory action confirms memory candidate.
- Reject memory action rejects memory candidate.
- create_memory action creates unconfirmed candidate only.
- Action with session_id creates UIInteractionEvent and ConversationTurn(observation).
- continue_task action creates or reuses conversation-native message flow, or safely noops if not enough data.
- invoke_tool with confirmation_required=true returns pending_confirmation.
- Unsupported action type returns safe failed/noop.
- Action payload sanitizer removes obvious secrets.
- Existing v0.8 reliability tests still pass.

Frontend checks:
- frontend build passes if dependencies are available.
- interaction components compile with new helper.

12. Run verification.
   Try:
   - python -m pytest backend/tests
   - python scripts/validate_app.py examples/apps/contract-review-agent
   - python scripts/validate_app.py examples/apps/sales-followup-agent
   - cd frontend && pnpm install && pnpm build, if pnpm/network are available
   - bash scripts/verify_local_demo.sh, if Docker/services are available

If commands cannot run because of environment limits, report honestly. Do not claim unverified success.

Definition of Done:
- Artifact actions execute through one backend endpoint.
- Action runtime creates UIInteractionEvent for important actions.
- Action runtime appends ConversationTurn(observation) when session_id is provided.
- Confirmation and memory actions work through the unified runtime.
- High-risk or confirmation-required tool actions are gated.
- Frontend interaction components use the unified action endpoint.
- /demo/telegram still works and passes session_id into action execution.
- Telegram callback path reuses action runtime where action context exists.
- Docs explain Artifact Action Runtime clearly.
- Tests cover action lifecycle and existing reliability checks still pass.
- Final summary includes files changed, tests run, results, and known limitations.
```
