# Tilo v0.6 Runtime Hardening and Developer Experience Plan

This document defines the next implementation milestone after v0.5 Round 2.

The current codebase now has the major runtime primitives:

```text
Agent App Manifest
Interaction Policy Runtime
Mini Surface Registry
ConversationSession / ConversationTurn
UIInteractionEvent
AgentContextBuilder
RichSurfaceLink / RichSurfaceTarget
Contract Review demo
```

This is a big step forward. Tilo is no longer just a demo. It is becoming a real agent app runtime.

The next milestone should not add a new large feature. It should harden the runtime and make it easier for external developers to understand, trust, and extend.

---

## 1. Current Code Review Summary

### 1.1 What is solid now

1. **Conversation runtime exists**
   - `ConversationSession` and `ConversationTurn` are now first-class backend models.
   - Conversation APIs exist for creating sessions and appending/retrieving turns.
   - Routes are registered through the main router list.

2. **Conversation-first demo is connected to backend sessions**
   - `/demo/telegram` creates or restores a conversation session.
   - Session id is stored in the URL query string.
   - The demo can append user messages, attachment turns, mini-surface turns, and observation turns.

3. **Agent context is session-aware**
   - `AgentContextBuilder` accepts `session_id`.
   - It can include recent conversation turns, recent user messages, recent agent messages, recent UI observations, confirmed memories, pending confirmations, active artifact summary, and last policy decision.

4. **Rich surface model exists**
   - `RichSurfaceTarget` and `RichSurfaceLink` are defined in the shared schema layer.
   - This supports the design principle that rich surfaces should be opened intentionally, not shown by default.

5. **Conversation remains the primary UX**
   - The current demo remains conversation-first rather than becoming a heavy dashboard.

### 1.2 Remaining issues

1. **Conversation logic is too route/component-owned**
   - `backend/app/api/routes/conversations.py` directly creates sessions and turns.
   - The frontend demo contains a lot of conversation orchestration logic.
   - A reusable framework should expose a `ConversationService` and a small client helper layer.

2. **Turn types are currently unvalidated strings**
   - `turn_type`, `channel`, rich surface `type`, and rich surface `source` are loose strings.
   - This is flexible, but easy for developers to misuse.
   - v0.6 should add typed constants/enums while keeping JSON flexibility where useful.

3. **Observation turn linkage is not guaranteed centrally**
   - The intended chain is:

   ```text
   frontend action -> UIInteractionEvent -> ConversationTurn(observation) -> AgentContext
   ```

   - Some paths append turns manually from the demo.
   - This should be centralized so future apps/channels do not forget to append observation turns.

4. **PromptBuilder context remains partial**
   - It includes recent UI observations.
   - It should also accept recent conversation turns in a concise, capped form.
   - The goal is not to dump the whole conversation into the prompt, but to make the agent aware of recent text turns and observation turns.

5. **Second app proof may still be shallow**
   - If `sales-followup-agent` exists, it should be tested and documented as a real example of the same runtime pattern.
   - If it does not exist yet, v0.6 should add it.
   - The second app should prove that Tilo is not just a contract-review demo.

6. **Developer experience is still not good enough for open-source adoption**
   - A new developer should be able to build a tiny app by copying an example folder.
   - Today, the underlying pieces exist, but the “happy path” is still not obvious enough.

---

## 2. v0.6 Goal

v0.6 should make Tilo feel like a small but real open-source framework.

Core goal:

```text
Make Tilo reliable and understandable enough for a developer to build their own agent app.
```

Do not redesign the demo.

Do not build a heavy dashboard.

Do not create a full workflow engine.

Focus on:

```text
runtime hardening + developer experience + reusable examples
```

---

## 3. P0: Add ConversationService

### 3.1 Why

Conversation runtime should not live mainly inside API route handlers or React components.

Add a backend service layer:

```text
backend/app/services/conversations/service.py
backend/app/services/conversations/schemas.py optional
```

### 3.2 Responsibilities

`ConversationService` should provide:

```python
create_or_get_session(...)
get_session(session_id)
append_turn(session_id, ...)
list_turns(session_id, limit=50)
append_user_message(...)
append_agent_message(...)
append_attachment(...)
append_mini_surface(...)
append_observation(...)
append_rich_surface_link(...)
find_by_external_thread(channel, external_thread_id, workspace_id)
```

### 3.3 Behavior

- API routes should call `ConversationService`.
- Telegram adapter/routes should call `ConversationService`.
- Future apps should not manually create `ConversationTurn` objects.

### 3.4 Acceptance criteria

- Existing conversation APIs still work.
- Route files become thinner.
- Tests cover service-level session creation, external-thread lookup, and turn append.

---

## 4. P0: Type the Runtime Primitives

### 4.1 Add constants or enums

Add typed runtime constants for:

```text
ConversationTurnType
ConversationRole
ConversationChannel
RichSurfaceTargetType
RichSurfaceSource
```

Suggested values:

```text
ConversationTurnType:
- user_message
- agent_message
- attachment
- mini_surface
- observation
- memory_candidate
- memory_confirmed
- system_event
- rich_surface_link

ConversationChannel:
- web
- telegram
- api

RichSurfaceTargetType:
- drawer
- page
- webview

RichSurfaceSource:
- policy
- user_action
- channel_fallback
```

### 4.2 Where

Backend:

```text
backend/app/services/conversations/constants.py
backend/app/services/surfaces/constants.py
```

Frontend:

```text
frontend/lib/conversationEvents.ts
frontend/lib/types.ts
```

### 4.3 Acceptance criteria

- API schema validates known turn types.
- Unknown turn types fail clearly or are only allowed through a documented escape hatch.
- Frontend demo uses shared string constants where practical.

---

## 5. P0: Centralize UIInteractionEvent -> Observation Turn

### 5.1 Why

This is one of Tilo's core ideas:

```text
UI actions become agent observations.
```

This must be hard to forget.

### 5.2 Required behavior

Add a helper method:

```python
ConversationService.append_observation_for_interaction(session_id, interaction_event)
```

It should create:

```text
ConversationTurn:
- turn_type = observation
- interaction_id = UIInteractionEvent.id
- artifact_id / run_id copied if available
- observation_payload_json = sanitized interaction payload
```

### 5.3 Integration points

Use this method in:

- web demo interaction paths
- Telegram callback path
- future channel adapters

### 5.4 Acceptance criteria

- Approve Revision creates both `UIInteractionEvent` and linked `ConversationTurn(observation)`.
- Remember action creates both `UIInteractionEvent` and linked `ConversationTurn(observation)`.
- Telegram callback creates both where session exists.
- Tests verify link consistency.

---

## 6. P0: AgentContextBridge v0.3

### 6.1 Goal

Make conversation turns actually useful to the agent.

`AgentContextBuilder` already supports `session_id`; v0.6 should tighten the shape and make it more useful.

### 6.2 Required output

`AgentContextBuilder.build(...)` should include:

```text
recent_conversation_turns
recent_user_messages
recent_agent_messages
recent_observation_turns
recent_ui_observations
confirmed_memories
pending_confirmations
active_artifact_summary
last_policy_decision
context_budget
```

### 6.3 PromptBuilder integration

Update `PromptBuilder.build(...)` to accept:

```python
recent_conversation_turns: list[dict] | None = None
recent_ui_observations: list[UIInteractionEvent] | None = None
```

Prompt shape should include a compact `conversation_context` block:

```json
{
  "conversation_context": {
    "recent_turns": [],
    "recent_observations": []
  }
}
```

### 6.4 Limits

Default limits:

```text
recent_conversation_turns: 12
recent_ui_observations: 5
content max length per turn: 500 chars
```

Do not dump full artifacts or long contract text into every prompt.

### 6.5 Acceptance criteria

- PromptBuilder tests show recent conversation turns are included and capped.
- UI observations are still separate from confirmed memories.
- Observation turns do not become memory unless explicitly confirmed.

---

## 7. P1: Add or Harden the Sales Follow-up Example App

### 7.1 Goal

Prove Tilo is a reusable runtime, not only a contract-review demo.

### 7.2 Required files

```text
examples/apps/sales-followup-agent/app.yaml
examples/apps/sales-followup-agent/interaction.policy.yaml
examples/fixtures/sales-followup-sample.json
```

### 7.3 Required app pattern

The app should demonstrate:

```text
Agent works autonomously
-> shows one MiniChoiceCard at a decision point
-> user action becomes observation
-> memory candidate is proposed only after preference signal
-> rich surface opens only when requested
```

### 7.4 Tests

- sales app manifest loads
- sales policy evaluates `MiniChoiceCard`
- full list action evaluates `SalesFollowupArtifact` rich surface
- undeclared surface fails validation

### 7.5 Documentation

`examples/apps/README.md` should explain why there are two apps and what they prove.

---

## 8. P1: Rich Surface Escalation Hardening

### 8.1 Goal

Make rich surfaces a reusable runtime concept.

### 8.2 Required work

- Add backend helper to create `RichSurfaceLink`.
- Add frontend helper to open target as drawer/page/webview.
- When rich surface is opened, append `ConversationTurn(rich_surface_link)`.
- Telegram renderer should map it to URL/WebApp button.

### 8.3 Acceptance criteria

- `Open Full Review` creates a rich surface link turn.
- `Open Artifact` can still navigate to `/artifacts/{id}`.
- Drawer/page/webview behaviors are clearly documented.

---

## 9. P1: Developer Experience Improvements

### 9.1 Add a “Build your first Tilo app” guide

Add:

```text
docs/BUILD_YOUR_FIRST_TILO_APP.md
```

It should walk through:

1. Copy `examples/apps/contract-review-agent`.
2. Rename app id.
3. Edit `app.yaml`.
4. Edit `interaction.policy.yaml`.
5. Choose mini surfaces.
6. Add sample fixture.
7. Run locally.
8. Test policy evaluation.

### 9.2 Add example cURL commands

Include:

```bash
curl http://localhost:8000/api/apps
curl http://localhost:8000/api/apps/contract-review-agent
curl -X POST http://localhost:8000/api/apps/contract-review-agent/interaction-policy/evaluate ...
curl -X POST http://localhost:8000/api/conversations ...
```

### 9.3 README update

README should highlight:

```text
Agent App Manifest
Interaction Policy
Mini Surface Registry
Conversation Runtime
Observation Context
Memory Lifecycle
```

---

## 10. P2: CLI Skeleton

### 10.1 Why

For open-source adoption, developers love quick scaffolding.

Add a very small CLI skeleton. Do not overbuild.

Possible command:

```bash
python -m app.cli init-app my-agent
```

or a script:

```bash
scripts/create_app.py my-agent
```

### 10.2 Scope

The command should create:

```text
examples/apps/my-agent/app.yaml
examples/apps/my-agent/interaction.policy.yaml
examples/apps/my-agent/README.md
```

### 10.3 Non-goal

Do not build a full production CLI yet.

This is only a developer-experience seed.

---

## 11. Testing Requirements

Add or improve tests for:

### Conversation service

- create session
- create or get by channel/external thread
- append each core turn type
- retrieve turns in chronological order
- reject invalid turn type

### Observation linkage

- UIInteractionEvent -> observation turn
- Telegram callback -> UIInteractionEvent -> observation turn
- observation turn appears in AgentContextBuilder

### Prompt context

- PromptBuilder includes recent conversation turns
- PromptBuilder caps long content
- PromptBuilder separates observations from memories

### Sales app

- manifest loads
- policy evaluates expected surfaces
- fixture loads

### Rich surface

- RichSurfaceLink validates target type/source
- Open Full Review appends rich surface link turn

---

## 12. Suggested Codex Prompt

```text
Read docs/V0_6_RUNTIME_HARDENING_AND_DEVELOPER_EXPERIENCE_PLAN.md.

Implement v0.6: Runtime Hardening and Developer Experience.

Do not redesign the UI.
Do not build a heavy dashboard.
Do not build a large workflow engine.
Focus on hardening the runtime and making it easier for developers to build their own Tilo app.

Implement in this order:

1. Add ConversationService.
   - Move session/turn creation logic out of API routes.
   - Support create_or_get_session, append_turn, list_turns, find_by_external_thread.

2. Add typed runtime constants/enums.
   - ConversationTurnType
   - ConversationChannel
   - RichSurfaceTargetType
   - RichSurfaceSource

3. Centralize UIInteractionEvent -> ConversationTurn(observation).
   - Add append_observation_for_interaction(session_id, event).
   - Use it in web demo and Telegram callback paths where session exists.

4. Upgrade AgentContextBuilder and PromptBuilder.
   - Include recent conversation turns and observation turns.
   - Keep limits: last 12 turns, last 5 observations, max 500 chars per turn.
   - Do not convert observations into memory automatically.

5. Add or harden Sales Follow-up example app.
   - app.yaml
   - interaction.policy.yaml
   - fixture JSON
   - tests proving MiniChoiceCard and rich surface policy decisions.

6. Harden Rich Surface Escalation.
   - Add helper/model for RichSurfaceLink creation.
   - Append rich_surface_link turn when Open Full Review is clicked.
   - Keep rich surfaces on-demand, not default.

7. Improve developer experience docs.
   - Add docs/BUILD_YOUR_FIRST_TILO_APP.md.
   - Update examples/apps/README.md.
   - Add cURL examples for apps, policies, and conversations.

8. Optional but useful: add a tiny app scaffold script.
   - scripts/create_app.py my-agent
   - Generates app.yaml, interaction.policy.yaml, README.md.

Constraints:
- Preserve deterministic and LLM modes.
- Preserve current contract review demo behavior.
- Preserve conversation-first UX.
- Preserve backend interaction policy as source of truth.
- No secrets in frontend or logs.
- Keep implementation lightweight and readable.
```

---

## 13. Definition of Done

v0.6 is done when:

1. Conversation runtime logic is mostly in `ConversationService`, not scattered across routes/components.
2. Core runtime primitives use typed constants/enums.
3. UI interaction events reliably create linked observation turns.
4. Agent context includes recent conversation turns and observations in a capped, safe shape.
5. Sales Follow-up demonstrates that the runtime is reusable.
6. Rich surface escalation is standardized.
7. A developer can follow a doc to create a new Tilo app.
8. The project feels more like an open-source framework and less like a single demo.
