# Tilo Integration Guide

This guide explains how developers should integrate Tilo into their own projects.

Tilo is not meant to force teams to rewrite their existing product. It should be adopted as an AI-native runtime layer that can sit beside an existing app, gradually taking over goal-first interaction, surface rendering, action execution, observation, and memory.

---

## 1. What Developers Get From Tilo

Developers use Tilo when they want their product to behave less like traditional SaaS and more like an AI-native app.

Tilo provides:

- conversation sessions and turns;
- app manifest and interaction policy;
- artifact generation and rendering contracts;
- artifact action runtime;
- UI interaction events;
- observation turns;
- memory candidate and confirmation lifecycle;
- deterministic local mode;
- example apps and validation scripts.

Tilo does not replace every part of a product. It provides the runtime layer for:

```text
Goal -> Surface -> Decision -> Action -> Memory
```

---

## 2. Integration Modes

Developers should be able to adopt Tilo at different depths.

### Mode A: Run Tilo as a standalone demo

Best for:

- evaluating the project;
- learning the runtime model;
- testing the contract-review example.

```bash
git clone https://github.com/adam2go/tilo-framework.git
cd tilo-framework
cp .env.example .env
docker compose up --build
```

Open:

```text
http://localhost:3000/demo
```

This mode is for evaluation only.

---

### Mode B: Use Tilo as a backend runtime sidecar

Best for teams that already have a product frontend and want to add AI-native runtime behavior.

Architecture:

```text
Existing frontend
       ↓
Tilo backend runtime
       ↓
Existing tools / MCP / internal APIs / databases
```

The existing app calls Tilo APIs:

- create conversation session;
- send a goal message;
- fetch artifacts;
- execute artifact actions;
- confirm memory candidates.

Key endpoints:

```text
POST /api/conversations
POST /api/conversations/{session_id}/messages
GET  /api/artifacts?workspace_id=...&task_id=...
POST /api/artifacts/{artifact_id}/actions/{action_id}
GET  /api/memories?workspace_id=...
POST /api/memories/{memory_id}/confirm
```

Use this mode when you want to keep your own UI but delegate runtime semantics to Tilo.

---

### Mode C: Embed Tilo interaction components

Best for teams building a new AI-native product surface but still using their own application shell.

Architecture:

```text
Existing app shell
       ↓
Tilo interaction components
       ↓
Tilo backend runtime
```

Developers can reuse:

- artifact renderer;
- mini surfaces;
- action execution helper;
- trace drawer pattern;
- memory confirmation UI.

The important rule:

```text
Frontend renders intent. Backend owns action semantics.
```

Do not copy business logic into frontend components. Use the artifact action runtime.

---

### Mode D: Build a Tilo App

Best for developers who want to define a reusable agent app inside the Tilo framework.

A Tilo app is a small declarative folder:

```text
examples/apps/my-agent/
  app.yaml
  interaction.policy.yaml
  README.md
  fixtures/
```

Create one:

```bash
python scripts/create_app.py my-agent
python scripts/validate_app.py examples/apps/my-agent
```

Then run Tilo locally and inspect:

```bash
docker compose up --build
curl http://localhost:8000/api/apps/my-agent
```

Use this mode when you want to package an agent workflow as a reusable AI-native app.

---

## 3. Recommended Adoption Path

For most developers, the recommended path is:

```text
Step 1: Run /demo locally
Step 2: Read one example app
Step 3: Create your own app.yaml and interaction.policy.yaml
Step 4: Call Tilo backend from your existing frontend
Step 5: Replace one existing form/dashboard flow with a goal-first Tilo flow
Step 6: Add memory confirmation only after the action loop works
```

Do not start by building a large dashboard. Start with one workflow where the user has a clear goal and one meaningful decision.

Good first use cases:

- contract review;
- sales follow-up;
- customer support response review;
- finance report explanation;
- HR policy Q&A with approval;
- document comparison;
- product requirement review.

Bad first use cases:

- rebuilding a full CRM;
- rebuilding an entire admin console;
- creating many disconnected dashboards;
- implementing multi-agent orchestration before one agent loop works.

---

## 4. Minimal API Integration Example

A product can integrate Tilo without using the Tilo frontend.

### 4.1 Create a session

```bash
curl -X POST http://localhost:8000/api/conversations \
  -H 'Content-Type: application/json' \
  -d '{
    "app_id":"contract-review-agent",
    "workspace_id":"workspace-id",
    "channel":"web"
  }'
```

### 4.2 Send a user goal

```bash
curl -X POST http://localhost:8000/api/conversations/session-id/messages \
  -H 'Content-Type: application/json' \
  -d '{
    "content":"Review this contract and flag risky liability clauses.",
    "attachments":[]
  }'
```

### 4.3 Fetch the artifact

```bash
curl "http://localhost:8000/api/artifacts?workspace_id=workspace-id&task_id=task-id"
```

### 4.4 Execute an action

```bash
curl -X POST http://localhost:8000/api/artifacts/artifact-id/actions/action-id \
  -H 'Content-Type: application/json' \
  -d '{
    "session_id":"session-id",
    "source":"web",
    "payload":{"choice":"approve"}
  }'
```

With `session_id`, Tilo records the user action as an observation turn.

### 4.5 Confirm memory

```bash
curl -X POST http://localhost:8000/api/memories/memory-id/confirm
```

Memory should remain confirmation-based. Tilo should not silently persist every observation as long-term memory.

---

## 5. How To Fit Tilo Into An Existing Product

A practical integration usually looks like this:

```text
Your product route
  -> user enters a goal
  -> your frontend creates or reuses a Tilo conversation session
  -> your frontend sends the goal to Tilo
  -> Tilo returns an artifact
  -> your frontend renders either:
       a) your own UI from the artifact spec, or
       b) Tilo's reference renderer
  -> user clicks an action
  -> your frontend calls Artifact Action Runtime
  -> Tilo records the observation and executes safe semantics
  -> your frontend refreshes the artifact / turns / memory candidate
```

The key integration boundary is the artifact and action contract, not a specific UI implementation.

---

## 6. What Should Be Stable For Developers

These are the contracts developers should depend on:

- app manifest structure;
- interaction policy decisions;
- conversation session and message APIs;
- artifact spec v1;
- artifact action runtime endpoint;
- action result shape;
- memory candidate and confirmation lifecycle;
- validation scripts.

These are reference implementations and may evolve faster:

- `/demo` UI;
- demo-specific components;
- visual styling;
- example fixture content;
- drawer layout;
- release demo copy.

---

## 7. What Not To Integrate Against

Do not build production code against:

- demo-only CSS class names;
- demo-specific React state machines;
- internal fixture IDs;
- old legacy demo routes;
- old milestone documents;
- raw trace display format.

Use stable API and runtime contracts instead.

---

## 8. Package Direction

Today Tilo is easiest to integrate by running the backend runtime and calling its APIs.

Future packaging should move toward:

```text
@tilo/react        reusable React components and hooks
@tilo/client       TypeScript API client
@tilo/schemas      shared artifact/action/event schemas
tilo-runtime       backend runtime package or service template
```

This is a packaging direction, not a promise that these packages exist today.

Until then, developers should use:

- REST APIs;
- example app folders;
- validation scripts;
- reference frontend components.

---

## 9. Integration Checklist

Before calling an integration complete, verify:

1. The user starts with a goal, not a dashboard form.
2. UI appears only when it helps the decision.
3. User actions go through Artifact Action Runtime.
4. The backend creates observation turns for meaningful actions.
5. Memory is proposed as a candidate, not silently confirmed.
6. The flow works without an API key in deterministic mode.
7. App manifest and policy pass validation.
8. The integration does not depend on demo-only code.
9. Runtime details are hidden by default and inspectable on demand.
10. The flow strengthens `Goal -> Surface -> Decision -> Action -> Memory`.
