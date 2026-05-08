# Demo Simplification Redesign

This document redesigns Tilo's public demo experience after v0.9.

The current `/demo/telegram` proves many runtime capabilities, but the page has become too complex. It shows too much framework machinery at once and can feel like a traditional SaaS dashboard.

That is not the product direction.

Tilo should feel like a modern AI product:

```text
Simple on the surface.
Structured underneath.
Inspectable when needed.
```

---

## 1. Design Diagnosis

The current demo tries to show too many things simultaneously:

- chat simulator;
- rich surface;
- developer inspector;
- live events;
- renderer decision;
- runtime mode;
- model diagnostics;
- interaction contract;
- durable observations;
- memory lifecycle;
- trace-like details.

This is useful for internal debugging, but overwhelming for first-time users.

The problem is not that these capabilities are wrong. The problem is that they are visible too early.

A good Tilo demo should not force users to understand ROAM, observations, renderer decisions, memory lifecycle, or interaction policy immediately.

Those are framework internals.

The user should first feel:

```text
I describe a goal.
Tilo produces a focused interactive result.
I make one or two decisions.
Tilo continues.
If I want, I can inspect how it worked.
```

---

## 2. New Demo Principle

Replace the current demo principle:

```text
Show the whole runtime in one page.
```

With:

```text
Show the product. Reveal the runtime.
```

This means:

- default view is minimal;
- framework internals are hidden by default;
- the surface appears only when useful;
- inspector opens intentionally;
- observations and memory are explainable, not constantly visible;
- demo should feel closer to ChatGPT / Claude / Perplexity-style simplicity than a SaaS admin console.

---

## 3. Target Layout

The new demo should use a single focused workspace.

Recommended route:

```text
/demo
```

Keep `/demo/telegram` as a compatibility route or redirect to `/demo` later.

### 3.1 Default view

```text
┌───────────────────────────────────────────────┐
│ Tilo                                          │
│ Build AI-native SaaS agents with ROAM runtime │
│                                               │
│  [ Ask Tilo anything...                    ]  │
│                                               │
│  Example chips:                               │
│  Contract Review · Sales Follow-up · Compare  │
└───────────────────────────────────────────────┘
```

Default screen should look almost empty.

No right inspector.
No dashboard panels.
No live event list.
No visible ROAM stages.
No raw debug data.

### 3.2 After user submits a goal

```text
┌───────────────────────────────────────────────┐
│ User goal                                     │
│ "Review this contract..."                    │
│                                               │
│ Tilo result                                   │
│ ┌───────────────────────────────────────────┐ │
│ │ Contract Review                           │ │
│ │ 3 high-risk issues found                  │ │
│ │                                           │ │
│ │ Primary decision                          │ │
│ │ Liability cap conflicts with indemnity... │ │
│ │                                           │ │
│ │ [Approve revision] [Adjust tone] [Open]   │ │
│ └───────────────────────────────────────────┘ │
│                                               │
│  Why this UI? · View trace · Open artifact    │
└───────────────────────────────────────────────┘
```

The result is centered and focused.

The user should see only:

- a concise summary;
- the key decision;
- 2–3 actions;
- optional links for details.

### 3.3 Inspector as drawer, not column

Developer details should move into a drawer:

```text
[Why this UI?]
```

Drawer content:

- Why Tilo rendered this surface;
- which interaction policy rule matched;
- what observation will be recorded;
- what action runtime endpoint will execute;
- whether memory candidate may be proposed.

A second drawer or tab can show:

```text
[View trace]
```

Trace drawer content:

- runtime mode;
- task/run id;
- artifact id;
- action result;
- conversation turns;
- observations;
- memory candidates.

This should not be visible by default.

---

## 4. UX Flow

### Step 1: Entry

User sees one input box and example chips.

Example chips:

```text
Review a contract
Draft sales follow-up
Compare agent frameworks
```

Clicking a chip fills or submits a sample prompt.

### Step 2: Agent working state

Use a compact status area:

```text
Tilo is reading the contract...
Tilo is deciding whether UI is needed...
Tilo is preparing a review surface...
```

Do not show logs by default.

### Step 3: Focused result card

For contract review, show one main card:

- title;
- risk count;
- primary issue;
- evidence snippet;
- recommended next action.

Secondary risks should be collapsed under:

```text
View all findings
```

### Step 4: Action

User clicks:

```text
Approve revision
```

Tilo shows:

```text
Revision draft created.
```

Then displays a compact revision card:

```text
Before
After
Why this change
```

### Step 5: Memory prompt

Memory prompt should be conversational and optional:

```text
Want me to remember this preference for future reviews?

"Prefer conservative but negotiation-friendly contract revisions."

[Remember] [Not now]
```

The user does not need to know this is ORID or memory lifecycle.

### Step 6: Explainability on demand

At any point, the user can click:

```text
Why this UI?
```

This reveals the framework logic.

---

## 5. Visual Direction

Target feeling:

```text
ChatGPT simplicity + Linear precision + Vercel polish.
```

Use:

- one-column centered layout;
- generous whitespace;
- minimal borders;
- soft cards;
- concise typography;
- action buttons with clear hierarchy;
- no permanent three-column layout.

Avoid:

- dashboard density;
- visible developer console by default;
- raw event names in main view;
- too many badges;
- too many panels;
- always-visible inspector;
- traditional SaaS admin feeling.

---

## 6. Information Architecture

### Default visible content

Visible by default:

- product title;
- single input;
- example chips;
- one focused result;
- primary actions;
- optional detail links.

### Hidden unless clicked

Hidden by default:

- interaction contract;
- renderer decision;
- durable observations;
- memory lifecycle details;
- runtime mode;
- model diagnostics;
- raw trace;
- conversation turns;
- action result JSON.

### Developer mode

Add a small toggle:

```text
Developer mode
```

When enabled:

- shows subtle metadata chips;
- enables drawer links;
- does not change the default layout into a dashboard.

Developer mode should enhance the simple product, not replace it.

---

## 7. Route Strategy

Recommended:

```text
/demo             new minimal public demo
/demo/telegram    compatibility route, can redirect or keep legacy hidden
```

README should point to:

```text
http://localhost:3000/demo
```

The old Telegram-like page can remain temporarily for internal debugging, but it should not be the primary public demo.

---

## 8. Component Strategy

Add new demo components:

```text
frontend/components/demo-minimal/
  MinimalDemoPage.tsx
  DemoPromptBox.tsx
  ExampleChips.tsx
  FocusedResultCard.tsx
  ContractReviewResult.tsx
  RevisionResultCard.tsx
  MemoryPromptCard.tsx
  ExplainDrawer.tsx
  TraceDrawer.tsx
  DeveloperModeToggle.tsx
```

Reuse existing runtime APIs:

- conversation-native message endpoint;
- artifact action runtime;
- artifact read endpoint;
- memory endpoint;
- trace endpoint;
- runtime capabilities endpoint.

Do not duplicate backend logic.

---

## 9. Backend Requirements

No major backend rewrite is required for the redesign.

The demo should use existing v0.9 backend capabilities:

```text
ConversationMessageService
ArtifactActionRuntime
UIInteractionEvent
ConversationTurn(observation)
ContextReflectionService
Memory candidates
```

If needed, add a lightweight endpoint:

```text
GET /api/demo/session/{session_id}/summary
```

But prefer composing existing APIs first.

---

## 10. Acceptance Criteria

The redesign is done when:

1. `/demo` exists as the primary public demo.
2. The default page is single-column and minimal.
3. A first-time user can understand the product without reading inspector panels.
4. Contract review flow works:
   - submit goal;
   - see focused result;
   - approve revision;
   - see revision draft;
   - optionally remember preference.
5. Developer details are hidden behind drawers or explicit links.
6. `/demo/telegram` is preserved or redirected without breaking existing tests.
7. README points to `/demo` instead of `/demo/telegram` if the new demo is ready.
8. No raw JSON or debug panels are visible by default.
9. The demo feels like a modern AI product, not a traditional SaaS backend.

---

## 11. Codex Implementation Notes

When implementing this redesign:

- do not delete the old demo until the new demo works;
- keep backend APIs unchanged unless absolutely needed;
- use existing Artifact Action Runtime for buttons;
- pass `session_id` to action execution;
- keep deterministic mode working without API key;
- make developer drawers optional;
- avoid a full UI rewrite outside the demo route;
- keep the page visually quiet.

The main goal is subtraction, not addition.
