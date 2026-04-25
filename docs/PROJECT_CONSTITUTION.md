# Tilo Project Constitution

This document is the highest-level project constitution for Tilo Framework.

All contributors, coding agents, and maintainers should read this before making major design decisions.

## 1. Mission

Tilo exists to help developers build AI-native SaaS agents that can remember long-term context, execute real work, ask humans for key decisions, and deliver results as interactive product artifacts.

Tilo should make it possible to build a new kind of software:

```text
not: SaaS + chatbot
but: Agent runtime + memory + tools + artifacts + human decision layer
```

## 2. North Star

The north star of Tilo is:

> Turn user intent into durable work outcomes.

A durable work outcome means:

- a task was created
- work was executed
- progress was traceable
- a useful artifact was produced
- human decisions were captured
- memory was updated for future work

## 3. Non-negotiable Product Loop

Tilo must protect this loop:

```text
Conversation
  -> Task
  -> Run
  -> Memory Recall
  -> Skill Selection
  -> Tool Execution
  -> Artifact Generation
  -> Human Confirmation
  -> Memory Update
  -> Future Improvement
```

Any implementation that bypasses this loop should be considered incomplete unless explicitly justified.

## 4. Core Principles

### 4.1 Agents should do work, not just talk

Tilo agents must be designed to execute tasks, call tools, generate structured outputs, and request decisions.

### 4.2 Memory should be inspectable and correctable

Users should know what the system remembers and be able to confirm, edit, delete, or reject memory.

### 4.3 Artifacts are first-class products

Markdown text alone is not enough for most workflows. Artifacts should be structured, persisted, rendered, and eventually editable.

### 4.4 Humans are decision makers

Humans should not manually operate every workflow step. They should approve, reject, edit, or steer meaningful decisions.

### 4.5 Safety is part of architecture

Tool permissions, confirmation gates, trace safety, secret handling, and prompt injection concerns must be designed from the beginning.

### 4.6 Framework before demo

Demos must use framework primitives. Do not build isolated demo code that cannot generalize.

### 4.7 Extensible but not bloated

Tilo should be modular and extensible, but v0.1 should avoid unnecessary enterprise complexity.

## 5. Core Domain Objects

These objects should remain central:

- Workspace
- Project
- Agent
- Task
- Run
- TraceStep
- Memory
- Skill
- Tool
- Artifact
- Confirmation

Do not replace these with vague generic records unless there is a strong reason.

## 6. Architectural Boundaries

### API Layer

Validates requests and calls services. It should not own core business logic.

### Runtime Layer

Owns task execution flow.

### Memory Layer

Owns memory extraction, storage, recall, confirmation, and visibility.

### Tool Layer

Owns tool registration, invocation, permission checks, and safety gates.

### Artifact Layer

Owns artifact schema generation, persistence, rendering contracts, and versioning.

### Inbox Layer

Owns human decisions and confirmation state.

## 7. Quality Bar

A feature is not complete if it only works in a hardcoded demo.

A feature is complete when:

- it uses the domain model
- it is connected to the runtime loop
- it has API support
- it has frontend visibility when user-facing
- it has traceability
- it respects security constraints
- it is documented when it changes architecture

## 8. Important Anti-patterns

Avoid:

- building only a chat page
- storing all outputs as Markdown
- storing memory as raw conversation history only
- hiding confirmations inside assistant text
- putting runtime logic in one giant endpoint
- creating demo-only logic that bypasses services
- exposing hidden chain-of-thought
- logging secrets
- implementing real external actions without confirmation
- adding large dependencies that erase Tilo's own domain model

## 9. v0.1 Success Criteria

v0.1 succeeds if it proves:

```text
A user can send a goal, Tilo can create a task/run, recall memory, generate trace, create an artifact, ask for confirmation, and produce memory candidates for future improvement.
```

Everything else is secondary.

## 10. Long-term Direction

Tilo should evolve toward:

- stronger long-term memory
- skill packages and skill marketplace
- richer artifact renderers
- message gateways such as Telegram, Slack, WeChat, Discord
- safer tool execution
- MCP integration
- browser and GUI automation
- project-level autonomous workspaces
- open ecosystem for AI-native SaaS agents

But every future step must preserve the core product loop.
