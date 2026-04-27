# Telegram In-chat Surface Redesign

This document defines the next UX direction for Tilo's public demo.

The current demo has been evolving from a three-column developer console toward a conversational experience. The next version should go further:

```text
The main page should feel like using Tilo inside Telegram.
```

The demo should be one chat-first interface where the agent can render small interactive cards inside the conversation, observe user actions, continue the conversation, and optionally open richer surfaces when the interaction is too complex for chat.

---

## 1. Core Decision

The primary demo UI should no longer be:

```text
left chat + center surface + right inspector
```

It should become:

```text
one Telegram-like conversation page
```

Generated UI components should appear inside the chat thread as interactive cards.

The user should be able to:

1. Type multiple messages.
2. Receive agent replies.
3. See generated mini interaction cards.
4. Click approve/edit/reject/remember buttons.
5. See the agent observe the click and continue.
6. Open a richer artifact page only when needed.

---

## 2. Telegram Capability Assumption

Telegram Bot API supports enough primitives for Tilo's first in-chat demo pattern:

- bot messages
- inline keyboards
- callback queries
- URL buttons
- Web App / Mini App buttons
- deep links
- file messages

This is enough for:

- lightweight approvals
- memory confirmations
- option selection
- opening artifact pages
- launching embedded web surfaces

However, Telegram chat itself is not suitable for every rich SaaS component.

Complex components such as full document editing, dense dashboards, complex comparison matrices, or long review surfaces should open a rich surface through:

- Telegram Web App / Mini App
- web artifact link
- hosted Tilo artifact page

So the rule is:

```text
Simple interactions render in chat.
Complex surfaces open from chat.
```

---

## 3. Product Thesis

The demo should communicate:

```text
Conversation is the main interface.
Mini surfaces appear inside the conversation.
Rich surfaces open only when needed.
Every UI action becomes an observation.
Memory closes the loop.
```

This is simpler and more natural than the previous three-column demo.

---

## 4. Recommended Public Demo Route

Keep:

```text
/demo/telegram
```

But the page title should be more general:

```text
Tilo Conversational Surface Demo
```

Subtitle:

```text
A Telegram-like agent session where UI cards appear inside the conversation and user actions become observations.
```

---

## 5. Page Layout

Use one primary chat container.

```text
┌───────────────────────────────────────────────┐
│ Tilo Bot · LLM mode badge · Inspector drawer   │
├───────────────────────────────────────────────┤
│                                               │
│ Bot message                                   │
│ User message                                  │
│ Bot message                                   │
│ Contract Review Mini Surface Card             │
│ Observation event                             │
│ Bot follow-up message                         │
│ Revision Draft Mini Card                      │
│ Memory Card                                   │
│                                               │
├───────────────────────────────────────────────┤
│ Sticky composer                               │
└───────────────────────────────────────────────┘
```

Optional:

- right drawer for Developer Inspector
- full artifact page opened by button
- mini app preview mode later

Do not show a permanent center panel or right panel by default.

---

## 6. Message Types

Implement the chat stream using typed turns.

```ts
type ChatTurn = {
  id: string;
  type:
    | "user_message"
    | "bot_message"
    | "mini_surface"
    | "observation"
    | "memory_card"
    | "system_event";
  content?: string;
  surface?: MiniSurface;
  observation?: Observation;
  created_at: string;
};
```

Mini surfaces are not separate pages. They are chat items.

---

## 7. Mini Surface Types

### 7.1 ContractReviewMiniSurface

A compact contract review card rendered inside the chat.

Should show:

- title
- risk summary
- 1 active risk node
- concise recommended revision
- primary buttons:
  - Approve Revision
  - Edit Direction
  - Open Full Review

Do not show all risks expanded.

### 7.2 RevisionDraftMiniSurface

Shows generated revision after approval.

Should show:

- changed clause summary
- before/after preview, compact
- buttons:
  - Make softer
  - Make stricter
  - Draft negotiation email
  - Open artifact

### 7.3 MemoryCandidateMiniSurface

Shows a memory proposal.

Should show:

- memory content
- why Tilo suggests remembering it
- buttons:
  - Remember
  - Edit
  - Not now

### 7.4 ToolCallMiniSurface

Shows tool action preview.

Should show:

- tool name
- action summary
- risk level
- buttons:
  - Approve
  - Reject
  - Details

---

## 8. Telegram Mapping

Each mini surface should have a Telegram-native approximation.

| Tilo Mini Surface | Telegram Representation |
|---|---|
| ContractReviewMiniSurface | message summary + inline keyboard + Open Full Review URL/WebApp button |
| RevisionDraftMiniSurface | message summary + action buttons + Open Artifact button |
| MemoryCandidateMiniSurface | message + Remember / Not now buttons |
| ToolCallMiniSurface | message + Approve / Reject buttons |
| Full RiskReviewPanel | open rich artifact page or Telegram Web App |
| EditableDocument | open rich artifact page or Telegram Web App |

This makes the web demo a close simulation of actual Telegram usage.

---

## 9. Required User Flow

### Step 1: User types a goal

```text
Review this contract for payment, liability, and termination risks.
```

### Step 2: Bot replies

```text
I found several risks. I created a compact review card below.
```

### Step 3: Mini surface appears in chat

Render `ContractReviewMiniSurface`.

### Step 4: User clicks Approve Revision

Actions:

1. Persist UIInteractionEvent.
2. Add observation turn:

```text
Observation: You approved the liability revision.
```

3. Bot replies:

```text
Got it. I’m generating a conservative revision draft.
```

4. Render `RevisionDraftMiniSurface`.

### Step 5: User continues with text

```text
Make the tone less aggressive.
```

Bot updates the revision card or appends a new version.

### Step 6: Memory proposal

Bot replies:

```text
I noticed you prefer conservative but negotiation-friendly revisions. Should I remember this?
```

Render `MemoryCandidateMiniSurface`.

### Step 7: User clicks Remember

Actions:

1. Persist UIInteractionEvent.
2. Confirm memory candidate.
3. Add observation turn.
4. Bot replies:

```text
Remembered. Future contract reviews will use this preference.
```

---

## 10. Developer Inspector

Developer information should exist, but not dominate the demo.

Move it into a drawer or modal:

```text
Developer Inspector
```

Inside the drawer:

- Interaction Contract
- Telegram mapping
- Live Events
- Runtime Mode
- Memory
- Trace

Default page should show only a small button:

```text
Inspector
```

---

## 11. Rich Surface Escalation

Not every interaction should stay inside chat.

If a component is too rich, show an `Open Full Review` button.

Rules:

```text
ApprovalCard -> in chat
MemoryCandidateCard -> in chat
ToolCallPreview -> in chat
RiskReviewPanel -> mini summary in chat + full artifact link
EditableDocument -> preview in chat + full artifact link
ComparisonMatrix -> summary in chat + full artifact link
MetricDashboard -> summary in chat + full artifact link
```

This matches how Telegram should be used in practice.

---

## 12. Backend Requirements

Use existing APIs where possible:

- `/api/messages`
- `/api/artifacts`
- `/api/interactions`
- `/api/confirmations`
- `/api/memories`
- `/api/runtime/capabilities`

Important actions must persist durable state:

- approve revision -> UIInteractionEvent + Confirmation
- remember preference -> UIInteractionEvent + Memory update
- text follow-up -> Message/Task/Run or demo conversation event

If full backend multi-turn orchestration is not ready, implement a lightweight demo conversation state first, but do not silently fake durable interaction events.

---

## 13. LLM Requirements

Preserve both modes:

```text
Deterministic mode: no API key required
LLM mode: OpenAI-compatible backend model call
```

The model should support follow-up user messages where possible.

At minimum:

- first user message generates contract review card
- follow-up text can append a bot response
- approval can generate revision card
- memory proposal can be created after revision

Do not expose API keys to frontend.

---

## 14. Visual Design

The page should feel like Telegram, but polished for a developer demo.

Use:

- one central chat shell
- message bubbles
- inline cards
- sticky composer
- compact topbar
- subtle runtime badge
- animated bot typing state
- smooth card insertion

Avoid:

- three-column dashboard
- permanent right inspector
- large disconnected surface panel
- raw JSON
- too many equal-weight cards

---

## 15. Acceptance Criteria

The redesign is done when:

1. `/demo/telegram` uses one chat-first page.
2. Users can type multiple messages.
3. Generated UI appears inline inside the chat stream.
4. UI clicks create visible observation messages.
5. Agent replies after observing clicks.
6. Memory proposal appears inline.
7. Developer Inspector is hidden by default in a drawer/modal.
8. Full artifact page is available through `Open Full Review`.
9. Deterministic and LLM modes still work.
10. A first-time user understands the demo without reading docs.

---

## 16. Codex Prompt

```text
Read docs/TELEGRAM_IN_CHAT_SURFACE_REDESIGN.md.

Redesign /demo/telegram so it feels like Tilo is used inside a Telegram-like chat.

Do not use the old three-column layout as the default.
Use one main chat thread where mini interactive surfaces appear inline.

Requirements:
1. Main page is a Telegram-like chat shell.
2. Support multi-turn text input in a sticky composer.
3. Render ContractReviewMiniSurface inside the chat after the first user message.
4. Render RevisionDraftMiniSurface after Approve Revision.
5. Render MemoryCandidateMiniSurface after revision.
6. UI clicks must create visible observation turns in the chat and persist UIInteractionEvent where supported.
7. Agent must reply after observing UI actions.
8. Developer Inspector moves into a drawer/modal.
9. Complex components have Open Full Review / Open Artifact buttons.
10. Preserve deterministic mode and LLM mode.
11. Preserve current backend APIs and Telegram adapter foundation.
12. No raw JSON in normal view.

Goal:
The demo should feel like a natural multi-turn Telegram conversation that grows small interactive SaaS surfaces when needed.
```
