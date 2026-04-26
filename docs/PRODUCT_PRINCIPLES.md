# Product Principles

This document defines the product principles for Tilo Framework. All coding agents and human contributors should read this before making major implementation decisions.

## 1. Product Thesis

Tilo is built on the belief that AI-native software will not be traditional SaaS with a chatbot bolted on.

Traditional SaaS:

```text
Human opens system -> finds feature -> fills form -> clicks buttons -> checks result -> decides next step
```

AI-native SaaS:

```text
Human states goal -> Agent renders an interactive surface -> Human interacts -> Agent acts -> System memorizes confirmed learning
```

Tilo should help developers build the second kind of product.

## 2. The Core Framework: ROAM Loop

Tilo's core interaction framework is the ROAM Loop:

```text
Render -> Observe -> Act -> Memorize
```

### Render

The agent renders an interactive artifact or component surface.

Examples:

- contract review panel
- approval card
- comparison matrix
- dashboard
- editable document
- task board
- memory review card

### Observe

The system observes structured user interaction and external results.

Examples:

- approve / reject
- edit
- select
- prioritize
- confirm memory
- reject recommendation
- tool call result

In Tilo, UI interaction is not temporary frontend state. It is structured observation.

### Act

The agent acts based on observations.

Examples:

- update artifact
- invoke tool
- create confirmation
- continue task
- ask clarification
- generate memory candidate
- generate skill candidate

### Memorize

The system extracts and stores confirmed learning.

Examples:

- user preference
- project fact
- decision
- reusable procedure
- feedback pattern

Memory must be inspectable and user-controllable.

## 3. What Tilo Is

Tilo is:

- An AI-native SaaS interaction framework.
- A ROAM Loop runtime.
- A memory-native agent framework.
- A framework for turning conversations into tasks, tasks into runs, runs into artifacts, artifacts into observations, and observations into future improvement.
- A system where agents can render interactive components, observe user decisions, act safely, and memorize confirmed learning.

## 4. What Tilo Is Not

Tilo is not:

- A chatbot wrapper.
- A thin LangChain demo.
- A generic multi-agent toy.
- A pure workflow engine.
- A pure memory database.
- A dashboard-only SaaS template.
- A static artifact renderer.

If an implementation only supports chat messages and Markdown responses, it is not enough.

If an implementation renders UI but does not turn user interaction into durable observations, it is not enough.

## 5. The Product Spine

Every important feature should support this loop:

```text
Conversation
  -> Task
  -> Run
  -> Render Artifact / Interaction Components
  -> Observe Human Interaction / Tool Results
  -> Act Safely Through Runtime / Tools / Confirmations
  -> Memorize Confirmed Learning
  -> Improve Future Runs
```

This is the product spine.

## 6. First-class Concepts

### Conversation

The command and steering layer. Users state goals, clarify intent, and respond to agent questions.

### Agent

The entity that understands goals, plans tasks, invokes tools, uses skills, generates artifacts, and asks for confirmation.

### Artifact

A structured product output and interaction surface: document, table, dashboard, kanban board, timeline, contract review view, comparison matrix, approval surface, or editable deliverable.

### Interaction Component

A reusable AI-native UI component generated or selected by the agent.

Examples:

- ApprovalCard
- RiskReviewPanel
- ComparisonMatrix
- MetricDashboard
- MemoryCandidateCard
- ToolCallPreview
- ActionQueue

### Observation

A durable record of user interaction or external state change.

Examples:

- UIInteractionEvent
- Confirmation decision
- Feedback
- Memory candidate decision
- Tool invocation result

### Memory

The long-term context layer. Memory includes user preferences, project facts, decisions, task experiences, and reusable procedures.

### Skill

A reusable capability package. Skills include instructions, templates, examples, schemas, and optional executable code.

### Tool

A callable connection to the external world: files, APIs, browser, MCP, databases, search, or custom actions.

### Inbox

The human decision layer. The Inbox collects confirmations, approvals, edits, and follow-up actions.

## 7. Product Quality Bar

Tilo should feel like a new AI-native SaaS framework, not a technical demo.

A good Tilo workflow should:

- Accept natural language input.
- Create a task and run.
- Render an interactive artifact surface.
- Make user actions observable and durable.
- Show progress and trace.
- Recall useful memory.
- Use tools when necessary.
- Ask for human confirmation at key moments.
- Update memory after confirmation.
- Make future tasks better.

## 8. Key UX Belief

The conversation page is the primary operating surface.

But the final value is not the chat transcript. The final value is the generated interaction surface and the durable decisions/memories it creates.

Tilo UI should prioritize:

- Goal input and task steering
- Interactive artifact delivery
- Human confirmation
- Memory transparency
- Traceability
- Low-friction interaction
- Reusable AI-native components

## 9. MVP Product Promise

The early product should prove one thing clearly:

> A user can give Tilo a goal, Tilo can render an interactive artifact, observe user interaction, act on it, and memorize confirmed learning for future runs.

Do not over-optimize a single module before this loop works.

## 10. Public Positioning

Tilo can be described publicly as:

```text
Tilo is an AI-native SaaS agent framework built around the ROAM Loop: Render, Observe, Act, Memorize.
```

Or in more practical terms:

```text
Tilo lets agents generate interactive SaaS-like pages, observe how humans use them, take safe actions, and learn from confirmed decisions.
```
