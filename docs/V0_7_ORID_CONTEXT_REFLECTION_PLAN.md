# Tilo v0.7: ORID Context Reflection and Runtime Closure Plan

This document defines the next implementation milestone after v0.6 runtime hardening.

v0.6 moved Tilo from a demo-like runtime toward a small open-source framework:

```text
Agent App Manifest
Interaction Policy Runtime
Mini Surface Registry
ConversationService
ConversationSession / ConversationTurn
UIInteractionEvent
AgentContextBuilder
PromptBuilder conversation_context
RichSurfaceLink / RichSurfaceTarget
Sales Follow-up example app
Developer onboarding docs
```

The next version should not add another large surface or a heavy dashboard. It should close the real runtime loop and introduce a lightweight ORID-inspired reflection layer so that user interactions become useful context, not just stored events.

---

## 1. Current Code Review Summary

### 1.1 What is solid now

1. **ConversationService exists and is meaningful**
   - Session creation, external-thread lookup, turn append, specialized append helpers, and observation-from-interaction helpers are centralized in `backend/app/services/conversations/service.py`.
   - API routes are thinner and now call `ConversationService` instead of directly creating all runtime objects.

2. **Core runtime primitives are typed**
   - Backend constants exist for `ConversationTurnType`, `ConversationRole`, and `ConversationChannel`.
   - Rich surface target/source constants exist.
   - Pydantic schemas now validate turn type, role, channel, and rich surface target/source.

3. **Conversation APIs are registered and tested**
   - Conversation routes are included in the router list.
   - Smoke tests cover session creation, external-thread lookup, turn append, and basic retrieval.

4. **AgentContextBuilder is session-aware**
   - It can load recent conversation turns when `session_id` is provided.
   - It separates recent user messages, agent messages, observation turns, UI observations, confirmed memories, pending confirmations, active artifact summary, and policy decision.

5. **PromptBuilder can accept conversation turns**
   - It supports `recent_conversation_turns` and emits a compact `conversation_context` block.
   - It caps turn count and content length, which is the right direction.

6. **Telegram mapping is no longer purely conceptual**
   - Telegram text creates or restores a conversation session by external chat id.
   - Telegram callbacks create `UIInteractionEvent` and linked observation turns when possible.
   - Telegram artifact links use `RichSurfaceLink` style behavior.

7. **Second app and developer docs exist**
   - `sales-followup-agent` exists as a second example app.
   - `docs/BUILD_YOUR_FIRST_TILO_APP.md` and `examples/apps/README.md` improve onboarding.
   - `scripts/create_app.py` provides a tiny scaffold path.

### 1.2 Important remaining issues

#### Issue 1: PromptBuilder supports conversation turns, but RunManager does not pass them

`PromptBuilder.build(...)` accepts `recent_conversation_turns`, and `AgentContextBuilder` can retrieve turns by `session_id`, but `RunManager.execute(...)` currently only passes `recent_ui_observations`.

This means the runtime has the pieces, but the actual agent execution loop still does not use recent conversation turns in normal message execution.

Required fix:

```text
Message/API/Channel -> session_id -> RunManager -> AgentContextBuilder -> PromptBuilder
```

The prompt should include compact recent conversation turns when a run is associated with a conversation session.

#### Issue 2: MessageFlowService has no session_id awareness

`/api/messages` creates a Task and Run without knowing which conversation session it belongs to.

The frontend demo works around this by manually appending turns, but the backend runtime should support a channel-native message endpoint such as:

```text
POST /api/conversations/{session_id}/messages
```

This endpoint should:

1. append the user message turn;
2. create task/run;
3. pass `session_id` into runtime execution;
4. append agent response / mini surface / rich surface turns where applicable.

#### Issue 3: There is no durable link from Run to ConversationSession

`ConversationTurn` can reference `run_id`, but `Run` itself does not know its conversation session.

This makes it harder for lower-level runtime services to retrieve conversation context without a caller manually passing `session_id`.

Recommended minimal fix:

```text
Add nullable session_id to Run or Task.
```

Prefer `Run.session_id` for runtime execution context.

#### Issue 4: UIInteractionEvent -> observation turn is centralized, but not automatic enough

`append_observation_for_interaction(...)` exists, and Telegram uses it. The web demo still has some orchestration in the component layer.

This is acceptable for the demo, but future apps should not need to remember this chain manually.

Recommended fix:

```text
POST /api/interactions should optionally accept session_id.
If session_id is provided, the backend should create the UIInteractionEvent and append the linked observation turn in one transaction-like service method.
```

#### Issue 5: Reset/replay semantics are still frontend-local

The web demo reset clears local state but keeps the existing session id in the URL. This is okay for a showcase, but not accurate for a durable conversation runtime.

Recommended fix:

```text
Reset Demo -> create a new ConversationSession and replace URL session_id.
Replay -> explicit demo-only behavior, not confused with persisted runtime reload.
```

#### Issue 6: ORID can improve observation quality, but should not replace ROAM

ORID is valuable as a reflection method, but it should sit inside the Observe/Act/Memorize part of ROAM. Tilo should not rebrand from ROAM to ORID.

Correct placement:

```text
ROAM = product/runtime loop
ORID = context reflection method inside Observe -> Act/Memorize
```

---

## 2. ORID Research Notes

ORID is a structured facilitation and reflection method:

```text
O — Objective: What happened? What facts or observations are available?
R — Reflective: How did the person react? What emotion, friction, preference, or signal appeared?
I — Interpretive: What does it mean? What pattern, need, risk, or principle can be inferred?
D — Decisional: What should happen next? What action, memory candidate, policy adjustment, or follow-up should be proposed?
```

For Tilo, ORID is useful because raw conversation turns and UI events are not enough. A click is only a fact. The runtime still needs to know why the click matters.

Example:

```text
Objective:
User clicked Approve Revision on clauses 8.1 / 8.2.

Reflective:
User accepted a conservative but negotiation-friendly direction.

Interpretive:
User may prefer contract revisions that reduce legal exposure without sounding hostile.

Decisional:
Propose a memory candidate: User prefers conservative but negotiation-friendly contract revisions.
```

This fits Tilo very well because Tilo already treats UI interaction as observation. ORID can be the missing interpretation layer between durable observation and durable memory.

---

## 3. Product Principle

Keep the original thesis:

```text
Agent by default. UI when necessary.
```

Add a second internal principle:

```text
Store facts, reflect before memory.
```

Do not automatically turn every event into memory.

The runtime should first classify and reflect:

```text
ConversationTurn / UIInteractionEvent
-> ORID Reflection
-> next action / policy signal / memory candidate
-> human confirmation
-> confirmed memory
```

---

## 4. v0.7 Goals

v0.7 has four goals:

1. Close the conversation context loop so actual agent runs receive session-aware conversation context.
2. Add an ORID-inspired `ContextReflectionService` for turning raw turns/events into structured reflection.
3. Make memory candidate creation more intentional and explainable.
4. Reduce frontend-owned runtime orchestration by adding a conversation-native message endpoint.

---

## 5. P0: Close Conversation Runtime Loop

### 5.1 Add session_id to runtime execution

Add `session_id` to either `Run` or `Task`.

Recommended:

```text
Run.session_id nullable string FK conversation_sessions.id
```

Why:

- A task may be reused conceptually, but each run belongs to one runtime execution context.
- Agent runtime services can retrieve session context through the run.

### 5.2 Update MessageFlowService

Update:

```python
MessageFlowService.create_task_run(..., session_id: str | None = None)
```

Behavior:

- Persist `run.session_id` if provided.
- Pass `session_id` into `RunManager.execute(...)`.

### 5.3 Update RunManager

Update:

```python
RunManager.execute(task, run, agent=None, session_id=None)
```

Behavior:

- Resolve session id from explicit argument or `run.session_id`.
- Build agent context through `AgentContextBuilder` when session id exists.
- Pass compact `recent_conversation_turns` and `recent_ui_observations` to `PromptBuilder`.
- Trace prompt context counts:

```json
{
  "recent_conversation_turn_count": 8,
  "recent_ui_observation_count": 3,
  "confirmed_memory_count": 2
}
```

### 5.4 Acceptance criteria

- A run created from a conversation session stores or receives `session_id`.
- `PromptBuilder` receives recent conversation turns in normal runtime execution.
- Trace output shows conversation turn count.
- Tests fail if `RunManager` drops conversation turns.

---

## 6. P0: Add Conversation-native Message Endpoint

Add:

```text
POST /api/conversations/{session_id}/messages
```

Input:

```json
{
  "content": "Review this contract and flag risky clauses.",
  "attachments": []
}
```

Behavior:

1. Validate session exists.
2. Append `user_message` turn.
3. Append `attachment` turns if provided.
4. Create Task and Run with session id.
5. Execute runtime.
6. Append an `agent_message` turn with safe result summary.
7. Append `rich_surface_link` turn if artifact exists.
8. Return task/run/artifact ids.

This endpoint should not fully replace `/api/messages` yet. Keep `/api/messages` for backward compatibility.

### Acceptance criteria

- Web demo can use this endpoint for initial messages.
- Telegram can use this endpoint or the same service path.
- Reloading session after sending message shows user and agent turns from backend state.

---

## 7. P0: ContextReflectionService with ORID

### 7.1 Add service

Add:

```text
backend/app/services/context_reflection/service.py
backend/app/services/context_reflection/schemas.py
```

### 7.2 Reflection input

Input should accept a bounded recent context object:

```python
reflect(
    session_id: str,
    workspace_id: str,
    project_id: str | None = None,
    artifact_id: str | None = None,
    trigger_event_id: str | None = None,
)
```

It should load:

- recent conversation turns;
- recent observation turns;
- recent UIInteractionEvents;
- active artifact summary;
- confirmed memories;
- pending confirmations.

### 7.3 Reflection output

Return a structured ORID object:

```json
{
  "objective": [
    {"source": "conversation_turn", "fact": "User approved revision for clauses 8.1 / 8.2."}
  ],
  "reflective": [
    {"signal": "preference", "summary": "User accepted conservative but negotiation-friendly wording."}
  ],
  "interpretive": [
    {"insight": "User prefers risk-reducing revisions that remain customer-friendly.", "confidence": 0.72}
  ],
  "decisional": [
    {"action": "propose_memory", "content": "User prefers conservative but negotiation-friendly contract revisions."}
  ]
}
```

### 7.4 Deterministic first

For v0.7, implement deterministic reflection rules first.

Examples:

- `artifact.action.approved` + `revision` payload -> preference signal.
- `channel.telegram.confirm_memory` -> confirmed memory event.
- user text containing tone direction -> preference candidate.
- repeated open_full_review -> user wants more evidence/detail.
- reject/not_now memory -> do not propose same memory again immediately.

LLM reflection can be added later, but should not block v0.7.

### 7.5 Persistence

Add optional persistence:

```text
ContextReflection
```

Suggested fields:

- id
- session_id
- workspace_id
- project_id nullable
- artifact_id nullable
- trigger_event_id nullable
- orid_json
- proposed_actions_json
- created_at

If persistence feels too heavy, v0.7 can start with service output plus trace records. But durable reflection is recommended because it helps explain why a memory candidate exists.

### 7.6 Acceptance criteria

- After approval/edit/follow-up, reflection returns O/R/I/D sections.
- Reflection does not directly create confirmed memory.
- Reflection can propose a memory candidate with explanation.
- Tests verify Objective facts are not mixed with inferred Interpretive claims.

---

## 8. P1: Memory Candidate via Reflection

### 8.1 Current problem

Memory candidates can exist, but the system does not yet clearly explain the reasoning path from user behavior to memory proposal.

### 8.2 Required behavior

Memory proposal should include ORID evidence:

```json
{
  "content": "User prefers conservative but negotiation-friendly contract revisions.",
  "source": "context_reflection",
  "evidence": {
    "objective": ["User approved revision for clauses 8.1 / 8.2."],
    "reflective": ["User accepted negotiation-friendly wording."],
    "interpretive": ["This looks like a reusable contract review preference."]
  }
}
```

### 8.3 UI behavior

MiniMemoryCard should be able to show a short explanation:

```text
Why remember this?
You approved a conservative revision and then asked for customer-friendly negotiation tone.
```

### 8.4 Acceptance criteria

- Memory candidate has `source_type = context_reflection` or `structured_payload.source = context_reflection`.
- Memory candidate UI can show why it was proposed.
- Rejecting memory does not erase the underlying observation/reflection.

---

## 9. P1: Web Demo Uses Backend Runtime More

Update `/demo/telegram` so it relies less on frontend-only orchestration.

Required changes:

- Use `POST /api/conversations/{session_id}/messages` for initial user message.
- Use `POST /api/interactions` with `session_id` if added, or keep using `/observations/from-interaction` as fallback.
- Reset creates a new conversation session and replaces URL.
- Keep local optimistic UI, but reconcile with backend turns after each major action.

Do not redesign the UI.

---

## 10. P1: Telegram Uses Shared Conversation Message Flow

Telegram currently creates session and appends user message before calling `MessageFlowService`.

After adding conversation-native message service, Telegram should reuse it.

Required behavior:

```text
Telegram text -> ConversationMessageService -> Task/Run -> AgentContext with session turns -> RichSurfaceLink
```

Acceptance criteria:

- Telegram text path and web conversation message path use the same backend service.
- Telegram callbacks still append observation turns.

---

## 11. P2: ORID in Docs

Add docs:

```text
docs/ORID_CONTEXT_REFLECTION.md
```

Explain:

- ORID is not replacing ROAM.
- ORID is used to interpret observations before memory/action.
- Examples for contract review and sales follow-up.
- How developers can plug custom reflection rules.

Update docs:

```text
docs/CONVERSATION_RUNTIME.md
docs/MEMORY.md
docs/BUILD_YOUR_FIRST_TILO_APP.md
```

Add one paragraph:

```text
Use ORID reflection when raw interactions need to become explainable memory candidates or next actions.
```

---

## 12. Testing Requirements

Add tests for:

### Runtime closure

- `POST /api/conversations/{session_id}/messages` appends user turn and agent turn.
- run stores or receives session id.
- `RunManager` passes recent conversation turns into `PromptBuilder`.
- trace includes recent conversation turn count.

### Context reflection

- approval event produces Objective fact and Decisional memory proposal.
- tone follow-up produces Reflective preference signal.
- reject memory does not produce immediate duplicate memory proposal.
- Objective facts do not contain inferred claims.

### Memory candidate explanation

- memory candidate created from reflection includes evidence in structured payload.
- MiniMemoryCard can render `why` explanation from memory payload.

### Web/Telegram shared path

- web conversation message and Telegram text produce equivalent session/turn/run behavior.
- Telegram callback appends linked observation turn.

---

## 13. Suggested Codex Prompt

```text
Read docs/V0_7_ORID_CONTEXT_REFLECTION_PLAN.md.

Implement v0.7: ORID Context Reflection and Runtime Closure.

Do not redesign the UI.
Do not replace ROAM with ORID.
ROAM remains the product/runtime loop. ORID is an internal reflection method for turning raw conversation turns and UI observations into explainable next actions and memory candidates.

Implement in this order:

1. Close the conversation context loop.
   - Add nullable session_id to Run, or otherwise persist run-to-session linkage.
   - Update MessageFlowService.create_task_run(..., session_id=None).
   - Update RunManager.execute(..., session_id=None) to load AgentContextBuilder with session_id.
   - Pass recent_conversation_turns and recent_ui_observations into PromptBuilder.
   - Trace recent_conversation_turn_count and recent_ui_observation_count.

2. Add POST /api/conversations/{session_id}/messages.
   - Append user_message turn.
   - Append attachment turns if provided.
   - Create Task/Run with session id.
   - Execute runtime.
   - Append agent_message and rich_surface_link turns where artifact exists.
   - Keep /api/messages backward compatible.

3. Add ContextReflectionService using ORID.
   - Add backend/app/services/context_reflection/service.py.
   - Produce objective, reflective, interpretive, decisional sections.
   - Start with deterministic rules.
   - Do not create confirmed memories automatically.

4. Wire reflection to memory candidates.
   - Memory candidates proposed from reflection should include structured_payload evidence.
   - Include a concise why-this-memory explanation.
   - Rejecting memory should preserve observation/reflection history.

5. Update web demo to use conversation-native message endpoint where possible.
   - Reset should create a new session id.
   - Keep optimistic UI, but reconcile with backend turns.

6. Update Telegram text path to share the same conversation message service.
   - Preserve callback observation linkage.

7. Add docs/ORID_CONTEXT_REFLECTION.md.
   - Explain ORID placement inside ROAM.
   - Add examples for contract review and sales follow-up.

8. Add tests.
   - Runtime closure tests.
   - ORID reflection tests.
   - Memory candidate explanation tests.
   - Web/Telegram shared path tests.

Constraints:
- Preserve deterministic and LLM modes.
- Preserve conversation-first UX.
- Preserve backend interaction policy as source of truth.
- No secrets in frontend, logs, traces, memories, or reflection payloads.
- Keep implementation lightweight and readable.
```

---

## 14. Definition of Done

v0.7 is done when:

1. Normal agent runs can see recent conversation turns from their session.
2. Web and Telegram can use a shared conversation-native message flow.
3. `UIInteractionEvent -> ConversationTurn(observation) -> AgentContext -> PromptBuilder` is actually closed.
4. ORID reflection produces explainable Objective / Reflective / Interpretive / Decisional output.
5. Memory candidates can explain why they were proposed.
6. ORID is documented as an internal reflection method, not a replacement for ROAM.
7. Tests cover the new closure points so future refactors do not silently break context memory.
