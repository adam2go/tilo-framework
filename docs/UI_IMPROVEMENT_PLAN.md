# Tilo UI Improvement Plan / UI 改进计划

The current Tilo Console proves the product loop, but the visual experience is still early. This document defines how to make the UI feel like a credible AI-native SaaS console.

当前 Tilo Console 已经跑通了核心产品闭环，但视觉和使用引导还比较早期。本文档用于指导后续把页面升级成更像正式开源项目 Demo 的 AI 原生 SaaS 控制台。

---

## 1. Current UI Diagnosis / 当前问题

### What works

- Single-page console already exists.
- User can send a task.
- Artifact can render in the center panel.
- Trace, Memory, Skills, Files tabs exist.
- Inbox confirmation items are visible.
- Demo prompts are available.

### Main problems

1. **Weak onboarding**  
   New users do not immediately know what to do.

2. **Unclear visual hierarchy**  
   Chat, Artifact, Trace, Memory, and Inbox have similar visual weight.

3. **Artifact does not feel like the final product yet**  
   The center panel should feel like a generated SaaS result page, not just a data preview.

4. **Inbox is hidden inside the context panel**  
   Human decisions are central to Tilo and deserve stronger presence.

5. **Memory review is too subtle**  
   Memory candidates should feel important and trustworthy, not like debug data.

6. **Demo prompts are too small**  
   Demo prompts should be onboarding cards with clear expected outcomes.

7. **No first-run story**  
   Users need a guided path: run demo -> inspect artifact -> approve confirmation -> confirm memory -> run again.

---

## 2. Target UX Direction

Tilo should feel like:

```text
AI-native workbench + result page generator + memory-aware agent console
```

It should not feel like:

```text
simple chatbot + JSON preview + debug sidebar
```

---

## 3. Recommended Layout vNext

```text
┌───────────────────────────────────────────────────────────────┐
│ Topbar: Tilo / Workspace / Project / Agent / Run status        │
├───────────────┬───────────────────────────────┬───────────────┤
│ Left Panel    │ Center Panel                  │ Right Panel   │
│               │                               │               │
│ Goal Input    │ Artifact Result Page          │ Context       │
│ Demo Cards    │                               │ - Trace       │
│ Run Progress  │ SaaS-like output              │ - Memory      │
│               │                               │ - Skills      │
│               │                               │ - Inbox       │
└───────────────┴───────────────────────────────┴───────────────┘
```

The center Artifact panel should be the hero area.

---

## 4. First-run Onboarding

When no artifact has been generated yet, show onboarding cards in the center panel.

Recommended cards:

### Contract Review

Title: `Review a contract`

Description: `Generate a risk review artifact with clauses, issues, and suggested revisions.`

Button: `Run demo`

### Sales Follow-up

Title: `Prioritize sales follow-up`

Description: `Generate a dashboard with customer recommendations and pending approvals.`

Button: `Run demo`

### Competitive Analysis

Title: `Analyze competitors`

Description: `Generate a structured comparison table and opportunity summary.`

Button: `Run demo`

---

## 5. Artifact Panel Improvements

Artifact panel should look like a result page.

Required improvements:

1. Add artifact header:
   - title
   - artifact type
   - status
   - version
   - linked run id

2. Add block styling:
   - cards with clear borders
   - risk item badges
   - table styling
   - metric cards
   - action buttons

3. Add artifact action bar:
   - approve related actions
   - regenerate placeholder
   - export placeholder
   - continue task placeholder

4. Add empty state:
   - explain what artifacts are
   - show demo cards

5. Add unsupported block fallback:
   - show safe message, not raw broken JSON

---

## 6. Chat / Task Panel Improvements

The left panel should help users understand what to do.

Recommended sections:

1. `What do you want Tilo to do?`
2. Textarea for goal input
3. Demo cards or prompt chips
4. `Run` button
5. Run progress strip
6. Current workspace/project/agent compact info

Do not show too much internal detail here.

---

## 7. Run Progress Improvements

Add visible step progress:

```text
✓ Task created
✓ Memory recalled
✓ Skills selected
✓ Tools invoked
✓ Artifact generated
✓ Confirmation created
✓ Memory candidates extracted
```

Use trace steps as the source when possible.

---

## 8. Right Context Panel Improvements

The right panel should be useful but not overwhelming.

### Trace tab

Show timeline-like steps:

- icon by status
- title
- summary
- timestamp if available

### Memory tab

Separate:

- Pending candidates
- Confirmed memories

Memory candidate card should include:

- type
- content
- confidence
- source
- confirm / reject / edit buttons

### Skills tab

Separate:

- Active skills
- Pending skill candidates

### Inbox tab

Inbox should show:

- pending decisions
- risk level if available
- source artifact/run
- approve / reject / edit actions

---

## 9. Dedicated Pages

Current single-page console is acceptable for early v0.2, but the next version should add:

```text
/artifacts/[id]
/memories
/skills
/inbox
/runs/[id]
```

These pages should not replace the console immediately, but provide deeper management views.

---

## 10. Visual Style Recommendation

Use a professional, modern SaaS style.

Recommended direction:

- light background: `#f8fafc`
- white cards
- subtle borders
- rounded corners
- soft shadows
- compact but readable typography
- blue / violet accent for agent intelligence
- amber / red for risks and confirmations
- green for confirmed memory and completed steps

Avoid:

- overly dark hacker UI
- raw debug-style panels everywhere
- playful toy styling
- dense tables as default

---

## 11. Suggested Component Refactor

Current `Console.tsx` is doing too much.

Refactor into:

```text
components/console/Console.tsx
components/console/TaskComposer.tsx
components/console/DemoPromptCards.tsx
components/console/RunProgress.tsx
components/artifact/ArtifactPanel.tsx
components/artifact/ArtifactHeader.tsx
components/artifact/ArtifactActionBar.tsx
components/context/ContextPanel.tsx
components/context/TraceTab.tsx
components/context/MemoryTab.tsx
components/context/SkillsTab.tsx
components/context/InboxTab.tsx
```

Goal:

- make each component readable
- make future UI polishing easier
- keep product concepts visible in code

---

## 12. UX Acceptance Criteria

The UI improvement is acceptable when:

1. A new user can understand what to do within 10 seconds.
2. Demo prompts are clear and outcome-oriented.
3. Artifact result is visually dominant.
4. Inbox decisions are obvious.
5. Memory candidates are easy to confirm or reject.
6. Trace steps explain what happened.
7. There is no raw JSON in normal user flow.
8. Empty states guide the user.
9. The page feels like an AI-native SaaS console, not a debug demo.

---

## 13. Suggested Codex Prompt

```text
Improve Tilo Console UI according to docs/UI_IMPROVEMENT_PLAN.md.

Do not change backend behavior unless necessary.

Focus on:
1. onboarding cards
2. clearer task composer
3. better artifact panel
4. stronger context tabs
5. visible run progress
6. memory candidate cards
7. inbox decision cards
8. component refactor

Preserve the core loop and existing API calls.
```
