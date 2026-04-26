# ROAM Workflow Demo Codex Requirements

This document defines the next frontend demo milestone for Tilo.

The goal is to create a public-facing demo experience that clearly proves Tilo is not a chatbot and not a static dashboard. Tilo should feel like a new AI-native SaaS interaction framework built around the ROAM Loop:

```text
Render -> Observe -> Act -> Memorize
```

The demo must be attractive enough for open-source promotion, README screenshots, short videos, and first-time developer onboarding.

---

## 1. Core Product Direction

The main demo should be a **ROAM Workflow Surface**.

This means the center area of the product is not just:

```text
a chat transcript
or a static artifact page
or a free-form canvas
```

It is:

```text
an agent-generated, sequential, interactive business workflow surface
```

The user starts with a goal in conversation. Tilo renders an interactive workflow. The user approves, edits, selects, or rejects important nodes. Those interactions become durable observations. The agent acts on them. Confirmed learning becomes memory.

---

## 2. Demo Strategy

The first public showcase should focus on one polished demo:

# Contract Review ROAM Demo

Reason:

- Easy to understand.
- Strong business value.
- Naturally requires review, approval, editing, and memory.
- Shows why Tilo is more than chat.
- Can demonstrate AI-native SaaS delivery clearly.

Secondary demos can remain available:

- Sales Follow-up
- Competitive Analysis

But they should not distract from the Contract Review showcase.

---

## 3. Target Information Architecture

Implement the main experience as:

```text
Landing / Demo Entry
  -> ROAM Workspace
      -> Conversation / Goal Steering
      -> Generated SaaS Workflow Surface
      -> Context / Trace / Memory / Inbox
  -> Artifact Detail Page
```

Recommended routes:

```text
/                         Public landing and demo entry
/console                  ROAM Workspace
/console?demo=contract    Contract Review demo entry
/artifacts/[id]           Standalone artifact result page
/memories                 Memory review page if already available
/inbox                    Decision center if already available
```

If existing routing differs, preserve existing routes but implement the same conceptual flow.

---

## 4. Main Page Layout

The main ROAM Workspace should use a three-zone layout:

```text
┌──────────────────────────────────────────────────────────────┐
│ Topbar: Tilo / Workspace / Project / Agent / ROAM Status      │
├────────────────┬──────────────────────────────┬──────────────┤
│ Conversation   │ Generated SaaS Workflow       │ Context      │
│                │ Surface                      │              │
│ Goal input     │ Workflow nodes               │ Trace        │
│ Demo cards     │ Interaction components       │ Memory       │
│ Run progress   │ Artifact preview             │ Inbox        │
│ Next actions   │ Approval/edit/select cards   │ Skills       │
└────────────────┴──────────────────────────────┴──────────────┘
```

### 4.1 Left zone: Conversation / Goal Steering

This should not feel like a generic chat sidebar.

Required sections:

1. Product mini headline:
   - `Build AI-native SaaS workflows with agents`
   - or `Describe a goal. Tilo renders a workflow.`

2. Goal composer:
   - textarea
   - send/run button
   - example prompt chips

3. Demo cards:
   - Contract Review
   - Sales Follow-up
   - Competitive Analysis

4. Run progress:
   - Task created
   - Memory recalled
   - Workflow rendered
   - Waiting for approval
   - Action executed
   - Memory updated

5. Next suggested action:
   - example: `Generate a conservative revision draft`

### 4.2 Center zone: Generated SaaS Workflow Surface

This is the hero area.

It must show a sequential workflow, not just cards randomly placed.

Required elements:

1. Artifact/workflow header:
   - title
   - artifact type
   - status
   - run id if available
   - version if available

2. ROAM status strip:

```text
Render -> Observe -> Act -> Memorize
```

3. Workflow timeline or stepper:

```text
1. Contract Input
2. Risk Review
3. Human Approval
4. Revision Draft
5. Memory Update
```

4. Interaction components embedded in the workflow:
   - RiskSummary
   - RiskReviewPanel
   - ApprovalCard
   - EditableDocumentPreview
   - MemoryCandidateCard
   - ActionQueue

5. Clear active step:
   - current node should be visually highlighted
   - completed nodes should show success state
   - future nodes should be muted

### 4.3 Right zone: Context / Control

Required tabs:

- Trace
- Memory
- Inbox
- Skills
- Observations

The right panel should show system transparency, not dominate the product.

If pending confirmations exist, show badge.
If memory candidates exist, show badge.

---

## 5. Visual Design Requirements

Current UI is not attractive enough. Redesign with a high-quality SaaS style.

Target feeling:

```text
Linear clarity + Vercel polish + Notion structure + Raycast speed
```

### 5.1 Visual style

Use:

- soft off-white background
- white elevated cards
- subtle slate borders
- 14-20px border radius
- compact but readable typography
- strong visual hierarchy
- indigo/violet/blue accent for intelligence
- amber/red for risk
- green for confirmed/completed
- subtle shadows, not heavy shadows

Avoid:

- raw gray admin dashboard look
- toy colors
- giant text blocks
- debug JSON in normal user flow
- unstyled HTML tables
- cramped spacing
- inconsistent buttons

### 5.2 Required visual states

Every workflow node/component should support:

- idle
- active
- completed
- pending confirmation
- failed

### 5.3 Open-source showcase quality

The page should be good enough for:

- README screenshot
- GitHub social preview image
- short product demo video
- first-time developer onboarding

A first-time visitor should understand within 10 seconds:

> Tilo lets agents generate interactive SaaS workflows, observe user actions, act safely, and memorize learning.

---

## 6. Required Interaction Components

Implement or polish these components.

### 6.1 RiskSummary

Purpose:

Show overall contract review result.

Required content:

- high risk count
- medium risk count
- low risk count
- short summary
- confidence or review status if available

### 6.2 RiskReviewPanel

Purpose:

Show clause-level risks.

Each risk item should include:

- clause title
- risk level
- issue summary
- suggested revision
- evidence/source text if available
- action buttons:
  - approve suggestion
  - edit suggestion
  - reject suggestion

### 6.3 ApprovalCard

Purpose:

Represent durable human decision.

Required content:

- decision title
- explanation
- risk level or permission level if available
- approve button
- reject button
- edit before approve button if supported

On action:

- call backend API
- persist UIInteractionEvent or Confirmation state
- update UI status

### 6.4 EditableDocumentPreview

Purpose:

Show generated revised contract or drafted output.

For now it can be a polished preview, not a full editor.

Required content:

- document title
- suggested changes highlighted
- version/status
- placeholder for future editing

### 6.5 MemoryCandidateCard

Purpose:

Show what Tilo wants to remember.

Required content:

- memory type
- content
- confidence
- source run/artifact if available
- confirm button
- reject button
- edit placeholder if not implemented

On confirm/reject:

- call backend API
- persist durable observation
- update status

### 6.6 ActionQueue

Purpose:

Show next available agent actions.

Examples:

- Generate conservative revision
- Export review report
- Continue with negotiation email
- Save review style as skill candidate

Actions should be clearly labeled as:

- safe
- needs approval
- coming soon

### 6.7 ToolCallPreview

Purpose:

Show tool action before execution.

Required content:

- tool name
- action summary
- permission level
- expected output
- confirmation button if high risk

### 6.8 ComparisonMatrix and MetricDashboard

These are secondary demo components.
They should exist or remain supported, but Contract Review components are higher priority.

---

## 7. Workflow Surface Behavior

The center surface should behave like a workflow, not a static report.

### 7.1 Workflow node model

Frontend can derive workflow nodes from artifact blocks, or use a simple local adapter.

Recommended node structure:

```ts
export type WorkflowNode = {
  id: string;
  title: string;
  description?: string;
  status: "idle" | "active" | "completed" | "pending" | "failed";
  roam_stage: "render" | "observe" | "act" | "memorize";
  component_type: string;
  artifact_block_id?: string;
};
```

### 7.2 Node ordering

For Contract Review demo, use this order:

```text
Contract Input
Risk Review
Human Approval
Revision Draft
Memory Update
Next Action
```

### 7.3 Interaction behavior

When user clicks an action:

1. Optimistically show loading state.
2. Call backend API.
3. Persist interaction event or confirmation/memory state.
4. Update node status.
5. Add/refresh trace or observation list if possible.
6. Do not only update local React state for important actions.

---

## 8. Landing Page Requirements

The first screen should explain the product before the user opens the console.

Required hero:

```text
Tilo Framework
Build AI-native SaaS agents with the ROAM Loop.

Render interactive workflows.
Observe human decisions.
Act through tools.
Memorize confirmed learning.
```

Required CTAs:

- Run Contract Review Demo
- Open ROAM Workspace
- View GitHub

Required sections:

1. ROAM Loop explanation
2. Contract Review showcase preview
3. Interaction component grid
4. Why not just chat?
5. Developer architecture overview

Keep landing clean. Do not overbuild marketing site.

---

## 9. Artifact Detail Page Requirements

`/artifacts/[id]` should feel like a standalone generated SaaS page.

Required sections:

- artifact header
- workflow/result content
- actions
- linked run
- memory refs
- observations if available
- trace link

The artifact detail page should be suitable as the final generated result.

---

## 10. Code Organization Requirements

Refactor frontend into clear component groups.

Recommended structure:

```text
frontend/components/roam/
  RoamWorkspace.tsx
  RoamStatusStrip.tsx
  WorkflowSurface.tsx
  WorkflowStepper.tsx
  WorkflowNodeCard.tsx

frontend/components/conversation/
  GoalComposer.tsx
  DemoPromptCards.tsx
  RunProgress.tsx
  NextActionCard.tsx

frontend/components/interaction/
  registry.tsx
  ApprovalCard.tsx
  RiskSummary.tsx
  RiskReviewPanel.tsx
  EditableDocumentPreview.tsx
  MemoryCandidateCard.tsx
  ActionQueue.tsx
  ToolCallPreview.tsx
  ComparisonMatrix.tsx
  MetricDashboard.tsx

frontend/components/context/
  ContextPanel.tsx
  TraceTab.tsx
  MemoryTab.tsx
  InboxTab.tsx
  SkillsTab.tsx
  ObservationsTab.tsx
```

Avoid giant `Console.tsx`.

If current files differ, migrate gradually but keep code readable.

---

## 11. Backend Integration Requirements

Preserve existing backend APIs when possible.

Important actions must call backend APIs:

- confirmation approval/rejection
- memory candidate confirmation/rejection
- interaction event creation
- artifact action execution if supported
- continue task if supported

If an API does not exist yet:

- create a thin API endpoint if appropriate
- or clearly mark frontend action as `coming soon`
- do not fake important durable state silently

---

## 12. Demo Data Requirements

The Contract Review demo should work even without real file upload.

Use a high-quality sample contract snippet and generated risk structure.

Sample risk categories:

- Payment terms
- Liability limitation
- Termination rights
- Confidentiality
- IP ownership

The demo should feel realistic, not like lorem ipsum.

---

## 13. Screenshots and README Readiness

After implementation, create or prepare:

- a clean default demo screen
- a populated Contract Review workflow screen
- an Artifact detail page screen

If image generation is not part of the repo, at least make the UI ready for screenshots.

README should eventually include:

```text
![Tilo ROAM Workflow Demo](./docs/assets/tilo-roam-workflow-demo.png)
```

Do not add fake screenshots unless they match current UI.

---

## 14. Acceptance Criteria

The demo is acceptable when:

1. The landing page clearly explains ROAM.
2. User can run Contract Review demo from landing or console.
3. Main workspace uses three-zone layout.
4. Center surface is a sequential workflow, not static cards.
5. At least these components are visually polished:
   - RiskSummary
   - RiskReviewPanel
   - ApprovalCard
   - EditableDocumentPreview
   - MemoryCandidateCard
   - ActionQueue
6. User interactions persist durable state where backend supports it.
7. Pending confirmation and memory candidates are visible.
8. The UI no longer feels like an admin/debug panel.
9. No raw JSON appears in normal user flow.
10. First-time user understands within 10 seconds that Tilo is not a chatbot.
11. The page is attractive enough for README screenshot and short demo video.

---

## 15. Suggested Codex Prompt

```text
Read these files first:
- docs/ROAM_LOOP.md
- docs/AI_NATIVE_INTERACTION_COMPONENTS.md
- docs/ROAM_CODEX_IMPLEMENTATION_PLAN.md
- docs/ROAM_WORKFLOW_DEMO_CODEX_REQUIREMENTS.md
- skills/roam-workflow-demo-designer/SKILL.md

Implement the ROAM Workflow Demo UI.

This is not a simple UI beautification task.
The goal is to make Tilo's public demo prove the ROAM Loop:
Render -> Observe -> Act -> Memorize.

Build a conversation-first workspace with a generated SaaS workflow surface.
Do not build a plain chatbot UI.
Do not build a full infinite canvas yet.

Prioritize the Contract Review demo.

Required output:
1. Landing / Demo Entry page
2. ROAM Workspace page
3. Generated SaaS Workflow Surface in the center
4. Polished Contract Review workflow
5. Interaction component registry
6. RiskSummary, RiskReviewPanel, ApprovalCard, EditableDocumentPreview, MemoryCandidateCard, ActionQueue
7. Right context panel with Trace, Memory, Inbox, Skills, Observations
8. Durable backend calls for confirmations, memory actions, and interaction events where supported

Design quality target:
Linear clarity + Vercel polish + Notion structure + Raycast speed.

The final UI should be suitable for GitHub README screenshots and a public open-source demo video.
```
