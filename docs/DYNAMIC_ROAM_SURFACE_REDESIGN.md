# Dynamic ROAM Surface Redesign Requirements

This document supersedes the previous dashboard-like ROAM demo direction.

The current demo UI is too complex and still feels like a traditional SaaS dashboard with agent-themed panels. It shows too many regions, tabs, cards, navigation items, and workflow blocks at once.

Tilo should not feel like:

```text
Traditional SaaS sidebar + dashboard cards + right debug panel
```

Tilo should feel like:

```text
A dynamic AI-native surface that changes as the agent understands intent, renders the next useful interface, observes the user's action, acts, and memorizes confirmed learning.
```

The goal is to make the UI feel less like a control panel and more like a living agent-generated work surface.

---

## 1. Core Diagnosis

The current UI has these problems:

1. Too much is visible at the same time.
2. The left navigation makes it feel like a traditional admin app.
3. The right context tabs make the product feel like a debug console.
4. The center workflow is too static and card-heavy.
5. The ROAM loop is shown as labels, but not experienced as motion.
6. User attention is split across sidebar, command panel, workflow, artifact, tabs, and inbox.
7. The interface does not feel driven by the user's current intent.
8. The generated SaaS surface does not feel dynamic enough.

The fix is not more polish. The fix is a different interaction model.

---

## 2. New Design Direction

Use a **Dynamic ROAM Surface**.

The interface should focus on one active step at a time:

```text
User intent -> Active generated surface -> Next decision/action -> Surface changes
```

Instead of showing every module at once, use progressive disclosure:

```text
Primary: current generated interaction surface
Secondary: compact conversation/input
Tertiary: collapsible memory/trace/inbox details
```

---

## 3. Recommended Layout

For the public demo, remove or hide the heavy app shell.

### Default public demo layout

```text
┌──────────────────────────────────────────────────────────────┐
│ Minimal topbar: Tilo · ROAM Loop · GitHub · Docs              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│                 Dynamic Generated Surface                    │
│                                                              │
│           [current active workflow component]                │
│                                                              │
│           [primary user decision / next action]              │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Compact conversation composer + suggested actions             │
└──────────────────────────────────────────────────────────────┘
```

Optional side details should be collapsed into drawers or small pills:

```text
Memory · Trace · Inbox · Observations
```

Do not show all of them as full panels by default.

---

## 4. Interaction Model

The UI should behave like a guided agent session.

### Step 1: User intent

Show a clean hero prompt:

```text
What should Tilo review, decide, or generate for you?
```

Demo CTA:

```text
Run Contract Review Demo
```

### Step 2: Agent renders current surface

The center should morph into the first generated surface:

```text
Contract Intake Surface
```

Not a full dashboard.

### Step 3: Agent advances to risk review

The surface transitions to:

```text
Risk Review Surface
```

Show only the risks that need attention, not all possible panels.

### Step 4: User decision

Show one clear decision card:

```text
Generate a conservative revision draft?
```

Primary actions:

- Approve
- Edit direction
- Reject

### Step 5: Agent acts

After approval, the surface changes to:

```text
Revision Draft Surface
```

Show generated edits and what changed.

### Step 6: Memorize

Show a memory confirmation surface:

```text
Should Tilo remember this review preference?
```

This completes the ROAM loop.

---

## 5. Visual Structure

Replace static dashboard density with staged surfaces.

### Use large active cards

Each active step should be a large, focused surface:

- Contract Intake Surface
- Risk Review Surface
- Approval Surface
- Revision Draft Surface
- Memory Surface

### Use timeline as subtle progress

A small top progress indicator is fine:

```text
Render → Observe → Act → Memorize
```

But it should not dominate the UI.

### Hide secondary complexity

Trace, memory, inbox, and observations should be accessible but not fully expanded by default.

Use:

- bottom drawer
- right drawer
- command palette
- small status pills

---

## 6. What to Remove or Hide in Demo Mode

For public demo mode, remove or hide by default:

- full left navigation sidebar
- full right tab panel
- always-visible long Inbox list
- all workspace/admin navigation
- dense multi-card workflow grid
- duplicate ROAM labels
- debug-like metadata
- raw internal counts unless useful

These can remain in a developer console mode, but they should not dominate the public demo.

---

## 7. Two Modes

Tilo should support two modes:

### 7.1 Showcase Mode

For open-source demo and README screenshots.

Characteristics:

- minimal navigation
- dynamic surface-centered layout
- guided ROAM session
- beautiful contract review flow
- progressive disclosure
- low cognitive load

Route suggestion:

```text
/demo
```

or:

```text
/console?mode=showcase&demo=contract
```

### 7.2 Developer Console Mode

For debugging and framework inspection.

Characteristics:

- full sidebar
- trace
- memory
- inbox
- observations
- workspace/project controls
- detailed internal state

Route suggestion:

```text
/console
```

Do not mix these two modes into one overwhelming screen.

---

## 8. Contract Review Showcase Flow

Implement the public demo as a staged flow.

### Stage 0: Intent

Surface:

```text
Describe the contract review goal
```

CTA:

```text
Run Contract Review Demo
```

### Stage 1: Render / Intake

Surface shows:

- contract title
- detected contract type
- review focus
- what Tilo will inspect

### Stage 2: Render / Risk Review

Surface shows:

- 3 important risks only
- one recommended review direction
- clean risk cards

Do not show too many risk items.

### Stage 3: Observe / Human Decision

Surface shows one main decision:

```text
Generate a conservative revision draft based on these risks?
```

Actions:

- Approve
- Adjust direction
- Skip

### Stage 4: Act / Revision Draft

Surface shows:

- before / after clause diff
- generated revision summary
- next possible action

### Stage 5: Memorize / Preference

Surface shows:

```text
Tilo noticed you prefer conservative risk handling and actionable revision suggestions. Remember this for future contract reviews?
```

Actions:

- Remember
- Edit memory
- Not now

---

## 9. Motion and Dynamic Feeling

The UI should feel alive, not static.

Use lightweight transitions:

- fade/slide between stages
- active card expansion
- completed step compression
- pending action pulse or subtle highlight
- streaming text placeholder where appropriate

Do not overdo animation.

The goal is to show that the surface changes as the agent moves through ROAM.

---

## 10. Component Requirements

### DynamicSurface

Main component that renders the active stage.

Props:

```ts
stage: RoamStage
artifact?: Artifact
activeBlock?: ArtifactBlock
onAction: (action) => Promise<void>
```

### RoamProgressPill

Small progress indicator:

```text
Render → Observe → Act → Memorize
```

### CompactComposer

Bottom or top compact input:

```text
Ask Tilo to change direction, continue, or refine the current result.
```

### ContextDrawer

Hidden by default. Opens Trace, Memory, Inbox, Observations.

### Stage Components

- IntentStage
- ContractIntakeStage
- RiskReviewStage
- ApprovalStage
- RevisionDraftStage
- MemoryStage

---

## 11. Design Quality Target

The showcase should feel more like:

```text
A guided AI product experience
```

Less like:

```text
A SaaS admin dashboard
```

Reference qualities:

- minimal first impression
- focused active task
- beautiful single-surface composition
- low cognitive load
- strong progressive disclosure
- visible but subtle agent progress

---

## 12. Acceptance Criteria

The redesign is acceptable when:

1. Public demo no longer shows heavy sidebar by default.
2. Public demo no longer shows full right debug panel by default.
3. The center dynamic surface dominates the screen.
4. Only one main user decision is shown at a time.
5. ROAM is experienced as stage progression, not just labels.
6. Trace/memory/inbox are accessible through drawers or compact pills.
7. Contract Review demo feels like a guided AI-native workflow.
8. A first-time user can understand what to do within 5 seconds.
9. The UI is screenshot-ready for README.
10. Developer console mode can still expose detailed state separately.

---

## 13. Codex Prompt

Use this prompt:

```text
Read docs/DYNAMIC_ROAM_SURFACE_REDESIGN.md first.

The current ROAM demo still feels like a traditional SaaS dashboard. Redesign it into a Dynamic ROAM Surface.

Do not simply polish the existing three-column dashboard.

Implement two modes:
1. Showcase Mode: minimal, dynamic, surface-first, guided Contract Review demo.
2. Developer Console Mode: detailed sidebar/context/debug panels for framework inspection.

For Showcase Mode:
- remove heavy sidebar by default
- hide full right context panel by default
- make the center Dynamic Generated Surface dominate the page
- guide the user through staged ROAM progression:
  Intent -> Contract Intake -> Risk Review -> Approval -> Revision Draft -> Memory
- show only one primary user decision at a time
- move Trace/Memory/Inbox/Observations into drawers or compact pills
- add smooth but subtle transitions between stages
- make the UI feel AI-native and alive, not like a static admin dashboard

Preserve existing backend APIs where possible.
Important interactions must still persist UIInteractionEvent, Confirmation, or Memory state when supported.
```
