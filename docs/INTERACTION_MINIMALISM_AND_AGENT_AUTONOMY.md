# Interaction Minimalism and Agent Autonomy

This document realigns Tilo with its original product thesis.

Tilo is not trying to make agents generate UI for everything.

Tilo exists because most agent frameworks still treat human-agent interaction as text-only. Tilo explores a more AI-native interaction model where UI appears only when it matters:

```text
Most work should be done autonomously by the agent.
Lightweight UI should appear only for confirmation, high-value information display, or human decision points.
User interaction should become observation and memory.
```

---

## 1. Core Principle

Tilo should follow this principle:

```text
Agent by default. UI when necessary.
```

Or:

```text
Autonomy first. Interaction at decision points.
```

The agent should normally continue working without asking the user to operate a SaaS interface.

UI should appear only when:

1. The agent needs human confirmation.
2. The agent needs to show important information that affects a decision.
3. The agent needs the user to choose among meaningful options.
4. The agent needs the user to approve a risky or irreversible action.
5. The agent wants to propose a memory that requires user control.
6. The agent needs to escalate from simple chat to a richer artifact surface.

Do not generate UI just because the system can.

---

## 2. What Tilo Is Optimizing For

Tilo is optimizing for AI-native work, not UI-heavy work.

Traditional SaaS:

```text
Human operates software step by step.
```

Bad agent UI:

```text
Agent turns every step into a card/button/page.
```

Tilo target:

```text
Agent works autonomously.
When a human decision is truly needed, Tilo renders a lightweight interaction.
That interaction becomes an observation.
Confirmed observations can become memory.
```

---

## 3. UI Trigger Policy

Every interaction component must have a clear reason to appear.

Recommended trigger categories:

### 3.1 Confirmation Trigger

Use when the agent wants to perform an action that requires human approval.

Examples:

- send an email
- modify a file
- generate a legal revision
- publish content
- call an external system
- approve a financial or HR action

Default component:

```text
ApprovalCard / ToolCallPreview
```

### 3.2 Important Information Trigger

Use when the agent has found information that the user should inspect before the agent continues.

Examples:

- high-risk contract clause
- financial anomaly
- compliance issue
- conflicting memory
- critical business decision

Default component:

```text
MiniRiskReviewCard / EvidenceCard / AlertCard
```

### 3.3 Choice Trigger

Use when the user must select a direction.

Examples:

- choose conservative vs balanced revision
- select customers to follow up
- choose a vendor
- pick a plan option

Default component:

```text
ChoiceCard / DecisionCard / MiniComparisonCard
```

### 3.4 Memory Trigger

Use when the system wants to remember something that affects future behavior.

Examples:

- user preference
- project fact
- decision pattern
- review style
- communication tone

Default component:

```text
MemoryCandidateCard
```

### 3.5 Rich Surface Escalation Trigger

Use when a chat card is not enough.

Examples:

- long document editing
- dense dashboard
- full comparison matrix
- multi-step approval workflow
- artifact review with evidence

Default component:

```text
Open Full Review / Open Artifact / Open Rich Surface
```

---

## 4. Interaction Budget

To avoid turning Tilo into a UI-heavy dashboard, each run should have an interaction budget.

Recommended defaults:

```text
Maximum visible mini surfaces per run: 3
Maximum confirmation prompts per run: 2
Maximum memory proposals per run: 1
Maximum rich surface escalation per run: 1
```

The agent can still work internally, but it should not overload the user.

If more interactions are needed, summarize and ask one grouped question.

---

## 5. Mini Surface vs Rich Surface

Tilo should define two user-facing surface levels.

### 5.1 Mini Surface

A lightweight interactive card inside chat.

Use for:

- approval
- rejection
- single choice
- memory confirmation
- tool preview
- compact risk summary
- next action selection

Mini surfaces should be short, focused, and action-oriented.

### 5.2 Rich Surface

A richer artifact page or embedded web surface.

Use only when mini surface is insufficient.

Use for:

- full document review
- editable contract revision
- dashboard
- complex comparison
- long report
- multi-step workflow

Rich surface should be opened intentionally from chat:

```text
Open Full Review
Open Artifact
Open Rich Surface
```

Do not show rich surfaces by default for every run.

---

## 6. Conversation-first Experience

The primary user experience should be conversation-first.

The normal flow:

```text
User: states goal
Agent: works autonomously
Agent: asks only when needed
Mini Surface: appears for confirmation/decision/important info
User: clicks or replies
System: records observation
Agent: continues
Memory Card: appears only when a memory needs confirmation
```

The UI should feel like a natural agent session, not a dashboard.

---

## 7. How UI Becomes Observation

When a user interacts with a mini surface or rich surface, Tilo should record a durable observation.

Examples:

```text
approval.clicked
choice.selected
risk.opened
revision.approved
memory.confirmed
tool_call.approved
```

These events should be available to:

- the current agent run
- future memory extraction
- trace/debug views
- interaction contract evaluation

This is the key Tilo difference.

A UI click is not just frontend state. It is an agent observation.

---

## 8. Relationship to ROAM

ROAM is still the core loop:

```text
Render -> Observe -> Act -> Memorize
```

But the Render step should be constrained:

```text
Render only when necessary.
```

The updated loop is:

```text
Autonomous work
  -> Render lightweight UI only at decision/info points
  -> Observe user interaction
  -> Act based on observation
  -> Memorize confirmed learning
```

---

## 9. What the Demo Should Prove

The demo should not prove that Tilo can render many UI components.

The demo should prove:

1. The agent can work autonomously.
2. The agent knows when human input is needed.
3. Lightweight UI appears at the right moment.
4. The user can confirm, choose, or inspect important information.
5. The agent observes that interaction and continues.
6. Confirmed preferences can become memory.

---

## 10. Required Demo Redesign

The current demo should be simplified into a conversation-first flow.

### 10.1 Default state

Show a chat-like page with a composer.

Do not show a dashboard, right inspector, or rich surface by default.

### 10.2 First user message

User enters:

```text
Review this contract for payment, liability, and termination risks.
```

### 10.3 Agent autonomous work

Agent replies:

```text
I reviewed the contract and found 3 issues worth your attention.
Most clauses look acceptable, but one liability clause needs confirmation before I generate a revision.
```

### 10.4 Lightweight information surface

Render one mini surface:

```text
Important issue: Liability limitation
Why it matters: the cap may not cover direct losses.
Recommended action: generate a conservative revision.

[Approve revision]
[Adjust direction]
[Open full review]
```

Do not show all risks expanded by default.

### 10.5 User action becomes observation

User clicks:

```text
Approve revision
```

Show:

```text
Observation: user approved conservative liability revision.
```

### 10.6 Agent continues

Agent replies:

```text
Approved. I generated a conservative revision draft.
```

Render a compact revision preview.

### 10.7 Memory only when appropriate

Agent proposes:

```text
Should I remember that you prefer conservative but negotiation-friendly contract revisions?
```

Render MemoryCandidateCard.

---

## 11. Developer Inspector

Developer inspector is still useful, but it should not dominate the user demo.

Move it into:

- drawer
- modal
- collapsible panel
- debug mode

Default user flow should hide it.

Inspector should show:

- why UI was triggered
- which interaction contract matched
- what observation was recorded
- what action followed
- what memory candidate was proposed

---

## 12. Codex Implementation Requirements

Implement this as the next demo milestone.

### 12.1 Main layout

- Replace the default three-column demo with a conversation-first page.
- Keep developer inspector hidden behind a drawer.
- Keep rich surface accessible through `Open Full Review`, but do not show it by default.

### 12.2 Multi-turn conversation

- Support user text input.
- Append user messages and agent messages to the same stream.
- Allow follow-up messages after UI interactions.

### 12.3 Interaction trigger discipline

- Do not render UI for every agent step.
- Render mini surfaces only for:
  - important information
  - confirmation
  - choice
  - memory
  - rich surface escalation

### 12.4 Mini surface components

Implement or adapt:

- MiniIssueCard
- MiniApprovalCard
- MiniRevisionPreview
- MiniMemoryCard
- MiniToolPreview

### 12.5 Observation feedback

- Every mini surface action should add a visible observation turn.
- Persist `UIInteractionEvent` where backend supports it.
- Agent should visibly continue after observing the action.

### 12.6 Memory flow

- Memory card should appear only after a meaningful interaction.
- It should not appear automatically for every message.

### 12.7 Rich surface escalation

- `Open Full Review` opens or reveals a richer artifact view.
- Rich view should not be default.

---

## 13. Acceptance Criteria

The redesign is acceptable when:

1. The default demo is conversation-first.
2. No permanent three-column dashboard is shown.
3. The agent appears to work autonomously before asking for input.
4. Mini UI appears only at a meaningful decision/info point.
5. User click creates visible observation.
6. Agent continues after observation.
7. Memory proposal appears only when appropriate.
8. Rich surface is available but not default.
9. Developer inspector is hidden by default.
10. The experience feels AI-native, not UI-heavy.

---

## 14. Suggested Codex Prompt

```text
Read docs/INTERACTION_MINIMALISM_AND_AGENT_AUTONOMY.md and docs/TELEGRAM_IN_CHAT_SURFACE_REDESIGN.md.

Realign the demo with Tilo's original product thesis:
Agent by default. UI when necessary.

The current demo still overemphasizes UI. Redesign /demo/telegram into a conversation-first agent session where lightweight UI appears only for important information, confirmation, choice, memory, or rich-surface escalation.

Requirements:
1. Default page is a Telegram-like chat conversation, not a three-column dashboard.
2. Agent should appear to work autonomously before asking for user input.
3. Render only one important mini surface at a time.
4. Mini surface should be used for the key issue/decision, not for every step.
5. User action creates visible observation and persists UIInteractionEvent where supported.
6. Agent continues after observing the action.
7. Memory card appears only after a meaningful approval or preference signal.
8. Rich Surface is opened through Open Full Review, not displayed by default.
9. Developer Inspector is hidden by default in a drawer/modal.
10. Preserve deterministic and LLM modes.
11. Preserve backend APIs and Telegram adapter foundation.
12. No raw JSON in normal flow.

Goal:
The demo should show that Tilo adds UI interaction to agent frameworks only when it improves human decision-making, not as a replacement for autonomous agent execution.
```
