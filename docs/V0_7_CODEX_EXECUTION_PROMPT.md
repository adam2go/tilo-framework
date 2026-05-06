# Tilo v0.7 Codex Execution Prompt

Use this prompt when asking Codex to implement v0.7.

```text
We are continuing development of Tilo Framework v0.7.

Repository:
adam2go/tilo-framework

First read:
- README.md
- docs/V0_7_ORID_CONTEXT_REFLECTION_PLAN.md
- docs/V0_6_RUNTIME_HARDENING_AND_DEVELOPER_EXPERIENCE_PLAN.md
- docs/CONVERSATION_RUNTIME.md
- docs/MEMORY.md
- docs/ROAM_LOOP.md
- docs/BUILD_YOUR_FIRST_TILO_APP.md

Implement v0.7: ORID Context Reflection and Runtime Closure.

Core principles:
- Do not redesign the UI.
- Do not turn Tilo into a heavy dashboard.
- Do not replace ROAM with ORID.
- ROAM remains the product/runtime loop: Render -> Observe -> Act -> Memorize.
- ORID is only an internal reflection method inside Observe/Act/Memorize.
- Store facts first, reflect before memory.
- Do not automatically turn every observation into confirmed memory.
- Preserve deterministic mode and LLM mode.
- Preserve the existing contract review demo behavior.
- Preserve backend interaction policy as the source of truth.
- Do not expose secrets in frontend, logs, traces, memories, or reflection payloads.
- Keep the implementation small, readable, and well-tested.

Background:
v0.6 already added ConversationService, ConversationSession / ConversationTurn, UIInteractionEvent, AgentContextBuilder, PromptBuilder conversation_context, RichSurfaceLink / RichSurfaceTarget, Telegram session mapping, sales-followup-agent, and developer onboarding docs.

The main remaining gap is that PromptBuilder can accept recent conversation turns, and AgentContextBuilder can load them, but RunManager currently does not pass session-level conversation turns into PromptBuilder during normal execution.

The target chain for v0.7 is:

ConversationSession
-> ConversationTurn / UIInteractionEvent
-> AgentContextBuilder
-> PromptBuilder
-> RunManager
-> ContextReflectionService
-> explainable memory candidate
-> human confirmation
-> confirmed memory

Implement in this order:

1. Close the conversation runtime loop.
   - Add nullable session_id to Run, preferably Run.session_id -> conversation_sessions.id.
   - Update lightweight schema compatibility migration so existing local databases can add runs.session_id safely.
   - Update MessageFlowService.create_task_run(..., session_id: str | None = None).
   - Persist run.session_id when provided.
   - Update RunManager.execute(task, run, agent=None, session_id=None).
   - Resolve session id from explicit argument first, then run.session_id.
   - If session id exists, use AgentContextBuilder to load session-aware context.
   - Pass recent_conversation_turns and recent_ui_observations into PromptBuilder.
   - Trace memory_count, skill_count, recent_ui_observation_count, recent_conversation_turn_count, and confirmed_memory_count if available.
   - Preserve /api/messages backward compatibility.

2. Add conversation-native message endpoint.
   - Add POST /api/conversations/{session_id}/messages.
   - Input: content and attachments.
   - Validate session exists.
   - Append user_message turn.
   - Append attachment turns if provided.
   - Create Task and Run with session_id.
   - Execute runtime with session_id.
   - Append agent_message turn with safe result summary.
   - Append rich_surface_link turn if artifact exists.
   - Return session_id, task_id, run_id, status, and artifact_id if any.
   - Prefer a reusable service path, not route-heavy logic.

3. Make UIInteractionEvent -> observation turn more automatic.
   - Update UIInteractionEventCreate to optionally accept session_id.
   - When POST /api/interactions receives session_id, create UIInteractionEvent and append linked ConversationTurn(observation) through ConversationService.append_observation_for_interaction.
   - Keep old behavior unchanged when session_id is omitted.
   - Sanitize payloads as currently done.

4. Add ContextReflectionService using ORID.
   - Add backend/app/services/context_reflection/__init__.py.
   - Add backend/app/services/context_reflection/schemas.py.
   - Add backend/app/services/context_reflection/service.py.
   - Implement deterministic reflection first; do not call an LLM in v0.7.
   - Output Objective, Reflective, Interpretive, and Decisional sections.
   - Objective must contain factual observations only.
   - Interpretive can contain inferred insight with confidence.
   - Decisional can propose actions, but must not directly confirm memory.

Required ORID rules:
- artifact.action.approved + revision-like payload -> approval fact, preference signal, possible revision-style insight, propose memory if reusable.
- user text containing tone direction such as “语气不要太强硬”, “customer-friendly”, “make it softer”, “more conservative” -> tone preference signal and possible memory proposal.
- repeated open_full_review / open_artifact -> user wants more evidence/detail.
- confirm_memory -> no duplicate memory proposal.
- reject_memory / not_now -> do not immediately propose the same memory again.

Preferred persistence:
- Add ContextReflection model if reasonable.
- Fields: id, session_id, workspace_id, project_id nullable, artifact_id nullable, trigger_event_id nullable, orid_json, proposed_actions_json, created_at.
- Add compatibility migration if the model/table is added.

5. Wire reflection to memory candidates.
   - When ContextReflectionService emits action=propose_memory, create or prepare a Memory candidate.
   - Do not confirm it automatically.
   - Use source_type=context_reflection or structured_payload.source=context_reflection.
   - Include structured_payload.why.
   - Include structured_payload.orid_evidence with objective, reflective, and interpretive evidence.
   - Avoid duplicate memory candidates for the same session and same content.
   - If the user rejected or skipped memory recently, do not immediately propose the same memory again.

6. Update MiniMemoryCard only if needed.
   - Show a concise “why remember this?” explanation from structured_payload.why.
   - Do not redesign the card.
   - Existing memory UI must still work.

7. Update the web demo carefully.
   - Use POST /api/conversations/{session_id}/messages for initial user message where possible.
   - Keep optimistic local UI.
   - Reconcile with backend conversation turns after backend response.
   - Pass session_id to POST /api/interactions when available.
   - Reset Demo should create a new ConversationSession and replace URL session_id.
   - Do not redesign /demo/telegram.

8. Update Telegram text path.
   - Telegram text should reuse the same conversation-native message service path as web.
   - Telegram callbacks should continue to create UIInteractionEvent and linked observation turns.
   - Preserve existing callback behavior.

9. Add docs.
   - Add docs/ORID_CONTEXT_REFLECTION.md.
   - Explain ORID does not replace ROAM.
   - Explain ORID is used inside Observe/Act/Memorize to interpret raw interactions.
   - Include contract review and sales follow-up examples.
   - Update docs/CONVERSATION_RUNTIME.md, docs/MEMORY.md, and docs/BUILD_YOUR_FIRST_TILO_APP.md with a short ORID reflection note.

10. Add tests.

Required tests:
- POST /api/conversations/{session_id}/messages appends user turn and agent turn.
- Run stores session_id.
- RunManager passes recent_conversation_turns into PromptBuilder.
- Trace includes recent_conversation_turn_count.
- POST /api/interactions with session_id creates UIInteractionEvent and linked observation ConversationTurn.
- POST /api/interactions without session_id still works.
- Approval event produces Objective fact and Decisional memory proposal.
- Tone follow-up produces Reflective preference signal.
- reject_memory / not_now prevents immediate duplicate memory proposal.
- Objective facts do not contain inferred claims.
- Reflection-based memory candidate includes structured_payload.source=context_reflection, why, and orid_evidence.
- Memory candidate remains candidate until user confirms.
- Web conversation message and Telegram text produce equivalent session/turn/run behavior.
- Telegram callback appends linked observation turn.
- Existing contract-review-agent and sales-followup-agent tests still pass.

Run tests:
- backend pytest
- frontend typecheck/build if package scripts exist
- If a command is unavailable, document that clearly in the final summary.

Definition of Done:
- Normal agent runs can see recent conversation turns from their session.
- Run has durable session linkage or equivalent reliable session context.
- Web and Telegram use a shared conversation-native message flow.
- UIInteractionEvent -> ConversationTurn(observation) -> AgentContextBuilder -> PromptBuilder is closed.
- ORID reflection produces explainable Objective / Reflective / Interpretive / Decisional output.
- Memory candidates can explain why they were proposed.
- Memory is not confirmed unless the user confirms it.
- Reset demo creates a new conversation session.
- ORID is documented as an internal reflection method inside ROAM.
- Tests cover the new runtime closure points.
- Existing contract review demo, sales follow-up app, deterministic mode, and /api/messages still work.

After implementation, provide a concise summary:
- What changed
- Files changed
- Tests run and results
- Known limitations or follow-up items
```
