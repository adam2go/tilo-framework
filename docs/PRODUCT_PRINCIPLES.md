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
Human states goal -> Agent plans and executes -> System presents artifact -> Human confirms key decisions
```

Tilo should help developers build the second kind of product.

## 2. What Tilo Is

Tilo is:

- A memory-native agent framework.
- An AI-native SaaS runtime.
- A framework for turning conversations into tasks, tasks into runs, runs into artifacts, and artifacts into decisions.
- A system where agents can remember users, projects, decisions, preferences, and reusable procedures.

## 3. What Tilo Is Not

Tilo is not:

- A chatbot wrapper.
- A thin LangChain demo.
- A generic multi-agent toy.
- A pure workflow engine.
- A pure memory database.
- A dashboard-only SaaS template.

If an implementation only supports chat messages and Markdown responses, it is not enough.

## 4. The Core Loop

Every important feature should support this loop:

```text
Conversation
  -> Task
  -> Run
  -> Memory Recall
  -> Tool Execution
  -> Artifact Generation
  -> Human Confirmation
  -> Memory Update
  -> Future Improvement
```

This loop is the product spine.

## 5. Six First-class Concepts

### Agent

The entity that understands goals, plans tasks, invokes tools, uses skills, generates artifacts, and asks for confirmation.

### Memory

The long-term context layer. Memory includes user preferences, project facts, decisions, task experiences, and reusable procedures.

### Skill

A reusable capability package. Skills include instructions, templates, examples, schemas, and optional executable code.

### Tool

A callable connection to the external world: files, APIs, browser, MCP, databases, search, or custom actions.

### Artifact

A structured product output: document, table, dashboard, kanban board, timeline, contract review view, customer card, or other interactive deliverable.

### Inbox

The human decision layer. The Inbox collects confirmations, approvals, edits, and follow-up actions.

## 6. Product Quality Bar

Tilo should feel like a product framework, not a technical demo.

A good Tilo workflow should:

- Accept natural language input.
- Create a task and run.
- Show progress and trace.
- Recall useful memory.
- Use tools when necessary.
- Generate structured artifacts.
- Ask for human confirmation at key moments.
- Update memory after completion.
- Make future tasks better.

## 7. Key UX Belief

The user should not operate every step. The user should understand outcomes and make decisions.

Tilo UI should prioritize:

- Task progress
- Artifact viewing and editing
- Human confirmation
- Memory transparency
- Traceability
- Low-friction interaction

## 8. MVP Product Promise

v0.1 should prove one thing clearly:

> A user can give Tilo a goal, and Tilo can turn it into a structured task, execute it, generate an artifact, ask for confirmation, and learn something for the future.

Do not over-optimize a single module before this loop works.
