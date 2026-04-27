# Unified Conversational Surface Redesign

This document defines the next major UX direction for Tilo's public demo.

The current Telegram-like demo has the right idea but still feels too mechanical:

```text
Left chat panel + center surface + right inspector
```

This makes chat and generated UI feel disconnected. Users may perceive it as a complex dashboard instead of a natural AI-native experience.

The next version should become a **Unified Conversational Surface**.

---

## 1. Core Problem

The current demo is too rigid:

1. Chat is separated from the generated UI.
2. The surface feels like a parallel panel rather than part of the conversation.
3. The demo is not truly multi-turn.
4. UI interactions are not visibly observed by the agent in the conversation.
5. Memory updates are shown as UI state, but not felt as part of the agent loop.
6. The developer inspector adds complexity too early.

The product thesis is still correct:

```text
Chat is the entry. Surface is the workspace. Interaction becomes memory.
```

But the experience should be more unified.

---

## 2. New Product Direction

Use one primary page:

```text
Unified Conversational Surface
```

Instead of three equal columns, use a single conversation-first workspace where messages and generated surfaces live in the same flow.

Recommended structure:

```text
┌─────────────────────────────────────────────────────────────┐
│ Minimal topbar: Tilo · ROAM Loop · Runtime Mode · GitHub     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Conversation Stream                                         │
│                                                             │
│ User message                                                │
│ Agent message                                               │
│ Generated Surface Card                                      │
│ User UI action                                              │
│ Agent observes + continues                                  │
│ Memory confirmation card                                    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Sticky Composer                                             │
└─────────────────────────────────────────────────────────────┘
```

Developer details should move into a collapsible drawer, not a permanent right panel.

---

## 3. UX Principle

The UI should feel like a conversation that can grow rich surfaces when needed.

Not:

```text
chat window next to a separate dashboard
```

But:

```text
chat message -> generated interactive surface -> user action -> agent response -> memory card
```

The generated UI should feel like an assistant-created object inside the conversation, similar to an artifact, not an unrelated SaaS panel.

---

## 4. Required Flow

The public demo should support a real multi-turn flow.

### Turn 1: User asks

User types:

```text
Review this contract for payment, liability, and termination risks.
```

### Turn 2: Agent responds and renders surface

Agent replies:

```text
I found several risks. I opened a focused review surface below.
```

Then Tilo renders an inline surface card:

```text
Contract Review Surface
- Risk summary
- Active risk node
- Recommended revision
- Approve / Edit / Reject
```

### Turn 3: User interacts with UI

User clicks:

```text
Approve Revision
```

This should create a visible observation message:

```text
Observation: user approved liability revision.
```

This observation can be shown as a small system event bubble or collapsed event row.

### Turn 4: Agent acts

Agent replies:

```text
Approved. I generated a conservative revision draft.
```

Then Tilo renders:

```text
Revision Draft Surface
```

### Turn 5: User continues with text

User can type:

```text
Make the tone less aggressive and more negotiation-friendly.
```

Agent updates the revision surface.

### Turn 6: Memory proposal

Agent replies:

```text
I noticed you prefer conservative but negotiation-friendly contract revisions. Should I remember this?
```

Then Tilo renders:

```text
MemoryCandidateCard
Remember / Edit / Not now
```

### Turn 7: User confirms memory

User clicks:

```text
Remember
```

Tilo persists memory and shows:

```text
Memory saved. Future contract reviews will use this preference.
```

---

## 5. Page Layout Requirements

### 5.1 One main stream

Use one central stream with max width around 960-1120px.

Message types:

- `user_message`
- `agent_message`
- `surface_card`
- `ui_observation`
- `memory_card`
- `tool_preview`
- `system_event`

### 5.2 Surface cards inside conversation

Generated surfaces should render inline in the stream.

The surface card can be large, but it should still feel attached to the conversation.

Surface card should include:

- title
- runtime mode badge
- ROAM stage badge
- primary generated component
- primary action
- secondary actions

### 5.3 Sticky composer

The composer should always allow multi-turn continuation.

Placeholder examples:

```text
Ask Tilo to revise, explain, continue, or remember something...
```

### 5.4 Collapsible developer drawer

Move these into a drawer:

- Interaction Contract
- Channel Routing
- Renderer Decision
- Live Events
- Runtime Mode
- Raw Debug

The default demo should not show the full inspector.

Provide a small button:

```text
Open developer inspector
```

### 5.5 Optional mini timeline

A subtle ROAM timeline may be shown near the top or attached to the active surface:

```text
Render → Observe → Act → Memorize
```

Do not let it dominate the page.

---

## 6. Interaction Requirements

### 6.1 Text input must be multi-turn

Users must be able to type multiple messages after the first run.

Example supported follow-ups:

```text
Make the revision more conservative.
Explain the liability risk in plain English.
Only focus on payment terms.
Draft a negotiation email.
Remember that I prefer balanced wording.
```

### 6.2 UI actions must become observations

When the user clicks UI actions like approve/reject/edit/remember:

1. Persist `UIInteractionEvent`.
2. Add an inline observation event to the stream.
3. Let the agent continue or update the surface.
4. Optionally generate memory candidate.

### 6.3 Agent should visibly observe UI actions

After a click, show an agent response such as:

```text
I observed your approval and generated the revision draft.
```

This is critical. The user must feel that the UI action entered the agent loop.

### 6.4 Surface should update, not just navigate

When user interacts, the surface should update in place or add the next surface card.

Avoid jumping to unrelated panels.

---

## 7. Runtime Requirements

### 7.1 Conversation state

The demo needs a lightweight conversation state model.

Minimum frontend state:

```ts
type DemoTurn = {
  id: string;
  type:
    | "user_message"
    | "agent_message"
    | "surface_card"
    | "ui_observation"
    | "memory_card"
    | "system_event";
  content?: string;
  artifact?: Artifact;
  surface?: DemoSurface;
  observation?: UIObservation;
  created_at: string;
};
```

### 7.2 Backend integration

Use existing backend APIs where possible:

- `/api/messages`
- `/api/artifacts`
- `/api/interactions`
- `/api/confirmations`
- `/api/memories`
- `/api/runtime/capabilities`

If full backend multi-turn orchestration is not ready, implement a clear demo state machine first, but do not fake durable interactions silently.

Important user actions must still call the backend.

### 7.3 Context passing

Follow-up messages should include enough context:

- current artifact id
- current run id
- recent user messages
- recent UI observations
- confirmed memories

This can be simple in v0.1.

---

## 8. Visual Design Direction

The page should feel:

```text
ChatGPT artifact experience + Telegram familiarity + Linear polish
```

Use:

- clean central stream
- minimal navigation
- large inline surface cards
- subtle animation when surface appears or updates
- clear distinction between user messages, agent messages, and system observations
- compact inspector drawer

Avoid:

- three equal heavy columns
- static dashboard look
- permanent right debug panel
- huge empty surface area
- disconnected panels
- too many visible controls at once

---

## 9. Demo Route

Recommended:

```text
/demo/telegram
```

But the experience should no longer visually emphasize Telegram too much.

Better public naming:

```text
Tilo Conversational Surface Demo
```

Subtitle:

```text
A chat-like agent session that renders interactive SaaS surfaces and learns from user actions.
```

---

## 10. Migration from Current Demo

Current components can be reused:

- ChatSimulator -> convert into ConversationStream
- RichSurfacePreview -> convert into inline SurfaceCard
- DeveloperInspector -> move into InspectorDrawer
- RuntimeMode card -> small badge + drawer detail
- Live Events -> inline observations + drawer detail

Do not throw away working backend integration.

---

## 11. Acceptance Criteria

The redesign is acceptable when:

1. The demo is one unified conversational page, not three equal panels.
2. Users can type multi-turn messages in the same composer.
3. Generated surfaces appear inline in the conversation stream.
4. UI actions create visible observations in the stream.
5. Agent visibly responds after observing UI interactions.
6. Memory confirmation appears as part of the conversation.
7. Developer inspector is available but collapsed by default.
8. Runtime mode is visible but not dominant.
9. The page feels simpler than the current Telegram-like dashboard.
10. A first-time user understands the loop in 5 seconds.

---

## 12. Suggested Codex Prompt

```text
Read docs/UNIFIED_CONVERSATIONAL_SURFACE_REDESIGN.md.

Redesign /demo/telegram into a Unified Conversational Surface.

The current three-column demo feels too rigid and disconnected. Replace it with one conversation-first page where generated surfaces appear inline inside the conversation stream.

Requirements:
1. Use a central conversation stream as the main layout.
2. Support multi-turn user text input through a sticky composer.
3. Render Contract Review Surface as an inline surface card after the agent response.
4. When users click UI actions such as Approve Revision or Remember, persist UIInteractionEvent and add a visible observation event into the stream.
5. After observing a UI action, show an agent response and update or append the next surface card.
6. Move Developer Inspector into a collapsible drawer, not a permanent right panel.
7. Keep runtime mode visible as a small badge.
8. Preserve LLM mode and deterministic fallback.
9. Preserve existing backend APIs and durable state calls.
10. Do not show raw JSON in normal view.

Goal:
The demo should feel like a natural multi-turn agent session that grows interactive SaaS surfaces when needed.
```

---

## 13. Summary

The next demo should prove this more directly:

```text
Conversation is the interface.
Generated surfaces are part of the conversation.
UI actions are observations.
Memory closes the loop.
```

This is more powerful and less confusing than showing separate chat, surface, and inspector panels at equal weight.
