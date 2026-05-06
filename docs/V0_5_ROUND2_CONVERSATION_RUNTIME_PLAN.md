# Tilo v0.5 Round 2: Conversation Runtime and Multi-app Plan

This document defines the next implementation milestone after Round 1.5 hardening.

Round 1.5 moved Tilo closer to a real interaction runtime:

```text
Agent App Manifest -> Interaction Policy -> Mini Surface Registry -> UI Observation -> Agent Context
```

Round 2 should now make this runtime durable, channel-friendly, and easier for developers to extend.

---

## 1. Current Assessment

The current codebase now has meaningful runtime foundations:

- `examples/apps/contract-review-agent/app.yaml`
- `examples/apps/contract-review-agent/interaction.policy.yaml`
- backend app manifest loader
- backend interaction policy service
- policy surface validation against manifest-declared surfaces
- stricter app/policy/sample path resolution
- frontend mini surface registry
- demo using backend policy evaluation with frontend fallback
- lightweight `AgentContextBuilder`
- `PromptBuilder` includes recent UI observations
- `RunManager` fetches recent UI observations and includes them in prompt context

This means Tilo is no longer just a UI demo. It is starting to become an agent app runtime.

However, the runtime is still missing one major piece:

```text
Conversation state is not yet durable and channel-native.
```

The next version should focus on backend conversation persistence and multi-app extensibility.

---

## 1.1 Round 1.5 Code Review Notes

A strict review of the latest Round 1.5 implementation found that the previous blocking issues have mostly been addressed.

### What is now solid

1. **Manifest and path safety improved**
   - `interaction_policy` is resolved inside the app directory.
   - sample inputs are restricted to the app directory or `examples/contracts`.
   - this is good enough for example-app loading in the current open-source milestone.

2. **Interaction policy validates against app manifest**
   - mini-surface policy outputs must be declared in `app.yaml` under `surfaces.mini`.
   - rich-surface policy outputs must be declared in `app.yaml` under `surfaces.rich`.
   - this prevents policy files from returning unknown frontend components.

3. **Backend policy is becoming the source of truth**
   - the backend now exposes interaction policy evaluation.
   - the frontend fallback can remain, but it should stay fallback-only.
   - future work should avoid adding new primary decision logic only in frontend code.

4. **Agent context bridge exists**
   - `AgentContextBuilder` now aggregates recent UI observations, pending confirmations, confirmed memories, active artifact summary, and the last policy decision.
   - this is a critical step toward making UI interactions visible to the agent runtime.

5. **Prompt context includes UI observations**
   - `PromptBuilder` accepts recent UI observations.
   - `RunManager` fetches recent UI observations and includes them in prompt construction.
   - this moves Tilo beyond a widget/demo model: UI actions can begin to affect future agent behavior.

6. **Tests now cover important runtime primitives**
   - manifest loading
   - apps API
   - policy evaluation
   - undeclared surface validation
   - unsafe sample path rejection
   - unsafe policy path rejection
   - prompt builder with UI observations
   - agent context builder with UI events, confirmed memories, and policy decision

### Remaining gaps before Tilo feels like a complete runtime

1. **Conversation is still not a backend runtime object**
   - The demo has a conversation-first UX, but conversation turns are not yet first-class backend state.
   - This blocks reliable reload, cross-channel continuity, Telegram thread mapping, and persistent multi-turn agent context.

2. **AgentContextBuilder is not yet session-aware**
   - It can aggregate workspace/project-level UI observations and memories.
   - It still needs to accept `session_id` and include recent conversation turns.

3. **Policy budgets are still caller-provided**
   - The code honestly marks the current budget counter source as caller supplied.
   - Round 2 should move toward backend-computed counters using `ConversationTurn` and/or `UIInteractionEvent`.

4. **The second app is still missing**
   - Contract review proves the idea.
   - A second app, such as Sales Follow-up Agent, is needed to prove that Tilo is reusable and not a contract-review-only framework.

### Decision

Round 1.5 is good enough to proceed to Round 2.

Do not do another UI redesign before Round 2.

The next milestone should focus on durable conversation runtime, session-aware agent context, rich surface escalation, Telegram mapping, and the second app example.

---

## 2. Product Principle

Keep the core thesis:

```text
Agent by default. UI when necessary.
```

Round 2 must not turn Tilo into a heavy dashboard.

The user-facing interaction model should remain:

```text
Conversation first.
Mini surfaces inline when human decision-making needs it.
Rich surfaces opened intentionally.
Developer inspector hidden by default.
```

---

## 3. Round 2 Goals

Round 2 has five goals:

1. Make conversation state durable.
2. Make web demo and Telegram callback share the same conversation/event model.
3. Standardize rich surface escalation.
4. Add a second app to prove Tilo is not contract-review-only.
5. Improve open-source readiness so developers can build their own app quickly.

---

## 4. P0: Backend Conversation Runtime

### 4.1 Why this matters

Currently, the demo has a conversation-first UX, but much of the conversation state is frontend-owned.

Tilo needs a backend conversation runtime so that:

- refresh can restore the session
- Telegram and Web can map to the same session concept
- UI observations can be attached to the same conversation
- future agent turns can use both text turns and UI observations
- app developers can build channel-agnostic agent apps

### 4.2 Data models

Add backend models:

```text
ConversationSession
ConversationTurn
```

Suggested fields:

```text
ConversationSession:
- id
- app_id
- workspace_id
- project_id nullable
- agent_id nullable
- channel
- external_thread_id nullable
- external_user_id nullable
- status
- metadata_json
- created_at
- updated_at

ConversationTurn:
- id
- session_id
- turn_type
- role nullable
- content nullable
- surface_type nullable
- surface_payload_json nullable
- observation_payload_json nullable
- artifact_id nullable
- run_id nullable
- task_id nullable
- interaction_id nullable
- confirmation_id nullable
- memory_id nullable
- policy_decision_json nullable
- created_at
```

Required turn types:

```text
user_message
agent_message
attachment
mini_surface
observation
memory_candidate
memory_confirmed
system_event
rich_surface_link
```

### 4.3 API endpoints

Add:

```text
POST /api/conversations
GET /api/conversations/{session_id}
POST /api/conversations/{session_id}/turns
GET /api/conversations/{session_id}/turns
```

Recommended optional endpoint:

```text
POST /api/conversations/{session_id}/messages
```

This endpoint can wrap the existing message/task/run flow and append turns automatically.

### 4.4 Session creation behavior

`POST /api/conversations` input:

```json
{
  "app_id": "contract-review-agent",
  "workspace_id": "...",
  "project_id": "...",
  "agent_id": "...",
  "channel": "web",
  "external_thread_id": null,
  "external_user_id": null,
  "metadata": {}
}
```

Return:

```json
{
  "id": "...",
  "app_id": "contract-review-agent",
  "channel": "web",
  "status": "active"
}
```

### 4.5 Turn append behavior

Turns should be append-only in this milestone.

Do not implement complex editing/deletion yet.

`POST /api/conversations/{session_id}/turns` should support:

- user message turn
- agent message turn
- attachment turn
- mini surface turn
- observation turn
- memory card turn
- rich surface link turn

### 4.6 Integration with existing UIInteractionEvent

When a UI action is persisted as `UIInteractionEvent`, also append a conversation turn:

```text
turn_type: observation
interaction_id: <UIInteractionEvent.id>
observation_payload_json: sanitized payload
```

This is essential.

A UI click must be visible as:

```text
frontend event -> UIInteractionEvent -> ConversationTurn(observation) -> AgentContext
```

---

## 5. P0: Agent Context Bridge v0.2

### 5.1 Current state

`AgentContextBuilder` already aggregates recent UI observations, pending confirmations, confirmed memories, active artifact summary, and policy decision.

Round 2 should connect it to conversation state.

### 5.2 Required additions

Update `AgentContextBuilder` to optionally accept `session_id`.

It should include:

```text
recent_conversation_turns
recent_user_messages
recent_agent_messages
recent_ui_observations
active_artifact_summary
pending_confirmations
confirmed_memories
last_policy_decision
```

### 5.3 PromptBuilder integration

`PromptBuilder` already includes recent UI observations.

Round 2 should prepare for conversation turns:

```text
PromptBuilder.build(..., recent_conversation_turns=None, recent_ui_observations=None)
```

Do not overload the prompt with every turn.

Default limit:

```text
recent_conversation_turns: last 12 turns
recent_ui_observations: last 5 observations
```

---

## 6. P1: Web Demo Uses Conversation Runtime

The current `/demo/telegram` UX should remain conversation-first.

Do not redesign it.

### 6.1 Required behavior

- On boot, create or restore a `ConversationSession`.
- When user sends initial message, append `user_message` and `attachment` turns.
- When agent responds, append `agent_message` turns.
- When MiniIssueCard appears, append `mini_surface` turn with policy decision.
- When user clicks Approve, append `observation` turn linked to `UIInteractionEvent`.
- When revision preview appears, append `mini_surface` turn.
- When memory candidate appears, append `memory_candidate` turn.
- On reload with session id, fetch turns and restore view.

### 6.2 URL behavior

Use query parameter:

```text
/demo/telegram?session_id=...
```

If no session id exists, create one and update URL using `history.replaceState`.

### 6.3 Fallback behavior

If conversation API fails, demo can fall back to local state, but should show non-blocking debug warning in inspector.

---

## 7. P1: Rich Surface Escalation Standard

### 7.1 Why this matters

Tilo should not show rich surfaces by default.

It should escalate only when the user wants more details or when mini surface is insufficient.

### 7.2 Add common type

Frontend type:

```ts
type RichSurfaceTarget = {
  type: "drawer" | "page" | "webview";
  artifactId?: string;
  url?: string;
  title?: string;
  source: "policy" | "user_action" | "channel_fallback";
};
```

Backend mirror if useful:

```text
RichSurfaceLink
```

### 7.3 Required behavior

- `Open Full Review` opens drawer first.
- `Open Artifact` navigates to `/artifacts/{id}`.
- Telegram uses URL or WebApp button.
- Rich surface open action should append `rich_surface_link` turn.

---

## 8. P1: Telegram Conversation Mapping

Telegram should map to the same runtime concepts.

### 8.1 Required behavior

When Telegram text message arrives:

1. Resolve or create `ConversationSession` by:

```text
channel = telegram
external_thread_id = chat_id
external_user_id = user_id
app_id = contract-review-agent by default
```

2. Append `user_message` turn.
3. Run existing task/run/artifact flow.
4. Append agent response and rich surface link turn.

When Telegram callback arrives:

1. Persist `UIInteractionEvent`.
2. Append `observation` turn to conversation if session exists.
3. If callback approves confirmation, append `memory_candidate` or `agent_message` as appropriate when supported.

### 8.2 Surface mapping

Use Mini Surface Registry mapping:

```text
MiniIssueCard -> message summary + inline keyboard
MiniApprovalCard -> message + approve/reject buttons
MiniMemoryCard -> message + remember/not now buttons
RichSurfaceLink -> URL/WebApp button
```

Do not block Round 2 on full Telegram Web App support.

---

## 9. P2: Second Example App — Sales Follow-up Agent

Round 2 should add a second app to prove the runtime is reusable.

### 9.1 Location

```text
examples/apps/sales-followup-agent/app.yaml
examples/apps/sales-followup-agent/interaction.policy.yaml
examples/fixtures/sales-followup-sample.json
```

### 9.2 App concept

User asks:

```text
帮我看看这周哪些客户应该优先跟进。
```

Agent works autonomously and shows only one decision mini surface:

```text
I found 3 customers worth following up this week.
Should I draft follow-up messages?
```

Actions:

```text
[Generate follow-up drafts]
[Change priority rule]
[Open full list]
```

Memory candidate after preference:

```text
User prefers low-pressure, relationship-first sales follow-up tone.
```

### 9.3 Policy examples

```yaml
rules:
  - id: priority-customers-need-confirmation
    when:
      artifact_type: sales_followup
      requires_user_decision: true
      category: outreach_priority
    decision: mini_surface
    surface: MiniChoiceCard
    reason: user_should_confirm_before_drafting_messages

  - id: normal-customer-no-ui
    when:
      artifact_type: sales_followup
      risk_level: low
    decision: no_ui
    reason: agent_can_continue_autonomously

  - id: open-full-customer-list
    when:
      user_action: open_full_list
    decision: rich_surface
    surface: SalesFollowupArtifact
    reason: user_requested_details
```

### 9.4 Important constraint

Do not build a full CRM.

This app is only an example proving reusable runtime:

```text
Manifest -> Policy -> Mini Surface -> Observation -> Memory
```

---

## 10. P2: Open-source Readiness

Add/update docs:

```text
docs/AGENT_APP_RUNTIME.md
docs/CONVERSATION_RUNTIME.md
docs/RICH_SURFACE_ESCALATION.md
examples/apps/README.md
```

README should point developers to:

```text
examples/apps/contract-review-agent
examples/apps/sales-followup-agent
```

Add a short “Build your own Tilo app” path:

```text
1. Create app.yaml
2. Create interaction.policy.yaml
3. Register mini surfaces
4. Add fixture/sample input
5. Run locally
```

---

## 11. Testing Requirements

Add tests for:

### Conversation runtime

- create conversation session
- append user message turn
- append mini surface turn
- append observation turn linked to `UIInteractionEvent`
- retrieve turns in order
- session lookup by channel/external_thread_id

### Agent context bridge

- context includes recent conversation turns
- context includes recent UI observations
- context includes confirmed memories
- context respects default limits

### Telegram mapping

- text message creates/fetches conversation session
- callback appends observation turn
- rich surface link uses artifact URL

### Second app

- sales follow-up manifest loads
- sales follow-up policy evaluates MiniChoiceCard
- invalid policy surface fails validation

---

## 12. Round 2 Codex Prompt

```text
Read docs/V0_5_ROUND2_CONVERSATION_RUNTIME_PLAN.md.

Implement v0.5 Round 2: Conversation Runtime and Multi-app Capability.

Do not redesign the UI.
Keep the product conversation-first.
Do not turn Tilo into a heavy dashboard.

Implement in this order:

1. Add backend ConversationSession and ConversationTurn models.
2. Add APIs:
   - POST /api/conversations
   - GET /api/conversations/{session_id}
   - POST /api/conversations/{session_id}/turns
   - GET /api/conversations/{session_id}/turns
3. Add session lookup support by channel + external_thread_id.
4. Update AgentContextBuilder to include recent conversation turns when session_id is provided.
5. Update PromptBuilder to accept recent conversation turns without overloading the prompt.
6. Make /demo/telegram create/restore a conversation session and persist key turns.
7. When UIInteractionEvent is created from the demo, append a linked observation turn.
8. Add common RichSurfaceTarget / RichSurfaceLink model.
9. Keep Open Full Review as drawer/page escalation, not default UI.
10. Map Telegram text/callback events to conversation session and observation turns where possible.
11. Add examples/apps/sales-followup-agent/app.yaml.
12. Add examples/apps/sales-followup-agent/interaction.policy.yaml.
13. Add minimal sales follow-up fixture data.
14. Add tests for conversation APIs, agent context bridge, Telegram mapping, rich surface link, and sales app policy.
15. Update docs/AGENT_APP_RUNTIME.md, docs/CONVERSATION_RUNTIME.md, docs/RICH_SURFACE_ESCALATION.md, and examples/apps/README.md.

Constraints:
- Preserve deterministic and LLM modes.
- Preserve existing contract review demo behavior.
- Preserve backend policy as source of truth.
- Do not expose secrets.
- Keep implementation small and readable.
```

---

## 13. Definition of Done

Round 2 is done when:

1. Conversation sessions and turns are persisted in backend.
2. `/demo/telegram` can restore conversation state by session id.
3. UI actions create both `UIInteractionEvent` and conversation observation turns.
4. Agent context includes recent conversation turns and UI observations.
5. Rich surface escalation is a common model, not demo-only logic.
6. Telegram text/callback events map into conversation runtime where possible.
7. A second app demonstrates that the runtime is reusable.
8. Tests cover core runtime behavior.
9. Docs make it obvious how developers can build their own app.
