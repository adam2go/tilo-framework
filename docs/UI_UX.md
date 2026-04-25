# UI and UX Guidelines

This document defines UI and UX expectations for Tilo Framework.

## 1. UI Product Positioning

The UI should feel like an AI-native SaaS console, not a toy chatbot.

The core UI purpose is to help users:

- give goals naturally
- monitor task progress
- inspect generated artifacts
- make key decisions
- manage memory
- understand execution traces

## 2. Default Layout

Use this layout as the default product direction:

```text
┌──────────────────────────────────────────────────────────┐
│ Topbar: workspace/project/agent/status                    │
├───────────────┬──────────────────────┬───────────────────┤
│ Sidebar       │ Main Artifact Area    │ Context Panel     │
│               │                      │                   │
│ Workspaces    │ Document/Table/etc.   │ Memory            │
│ Projects      │                      │ Trace             │
│ Agents        │                      │ Skills            │
│ Inbox         │                      │ Files             │
├───────────────┴──────────────────────┴───────────────────┤
│ Bottom or left panel: Chat / Task Input / Run Progress     │
└──────────────────────────────────────────────────────────┘
```

For v0.1, a simpler layout is acceptable:

```text
Sidebar | Chat Panel | Artifact Panel | Context Panel
```

## 3. Required Pages

- Home / default workspace
- Project workspace page
- Agent list and editor
- Inbox page
- Memory page
- Skill page
- Artifact detail page

## 4. Required Components

### Layout

- AppShell
- Sidebar
- Topbar
- MainContent
- ContextPanel

### Chat

- ChatPanel
- MessageBubble
- TaskInput
- RunProgress

### Artifact

- ArtifactRenderer
- DocumentArtifact
- TableArtifact
- DashboardArtifact
- KanbanArtifact
- TimelineArtifact
- ContractReviewArtifact

### Inbox

- InboxList
- InboxItem
- ConfirmationCard
- ApprovalActions

### Memory

- MemoryPanel
- MemoryCard
- MemoryEditor
- MemoryCandidateCard

### Trace

- TracePanel
- TraceStep

### Skills

- SkillList
- SkillCard
- SkillEditor

## 5. Visual Style

Use a clean, modern, professional SaaS style:

- generous spacing
- readable typography
- cards for structured information
- clear status indicators
- subtle borders and shadows
- avoid clutter
- avoid overly playful UI

The product should feel credible for professional workflows such as legal, sales, HR, finance, and product work.

## 6. Interaction Principles

### Show progress

Long-running agent tasks must show progress. Do not leave users staring at a blank screen.

### Separate chat from output

Chat is for command and clarification. Artifact is for final structured output.

### Make confirmations explicit

Important decisions should appear as durable confirmation cards, not hidden inside long assistant text.

### Make memory visible

Users should be able to inspect what the agent remembers.

### Make trace understandable

Trace should show execution progress in human-readable summaries.

## 7. Artifact Rendering

Artifact rendering should be schema-driven.

The UI should dispatch by:

- artifact_type
- block.type

Do not render all outputs as raw JSON or raw Markdown.

## 8. Inbox UX

Inbox is the human decision center.

Inbox items should show:

- title
- description
- source task/run
- risk level if applicable
- recommended action
- approve/reject/edit buttons
- status

## 9. Memory UX

Memory cards should show:

- type
- content
- source
- confidence
- confirmed/unconfirmed status
- created date
- edit/delete/confirm actions

## 10. Empty States

Every major page should have useful empty states.

Examples:

- No artifacts yet: "Start a task to generate your first artifact."
- No memories yet: "Tilo will suggest memories after tasks are completed."
- No inbox items: "No decisions pending."

## 11. Avoid

Do not:

- build only a centered chat box
- dump long JSON into the main UI
- make the artifact panel an afterthought
- hide confirmation actions in chat text
- ignore memory and trace panels
- overcomplicate onboarding before the first task works
