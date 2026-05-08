# Tilo v1.0 Framework Release Plan

v1.0 is the framework release milestone.

After v0.9, Tilo already has the main runtime pieces:

- app manifest and interaction policy;
- conversation runtime;
- artifact spec and renderer;
- artifact action runtime;
- UI interaction events;
- observation turns;
- context reflection;
- memory candidates;
- example apps;
- verification scripts;
- CI foundation.

v1.0 should not be a large feature dump. It should make Tilo feel like a coherent AI-native framework with one clean demo, one clear developer path, and one stable runtime contract.

Before implementation, read:

```text
docs/AI_NATIVE_FRAMEWORK_PRINCIPLES.md
```

That document is a hard product constraint, not optional background.

---

## 1. Positioning

Tilo v1.0 should communicate:

```text
Tilo is a framework for building AI-native SaaS agents.

Agents can render focused interactive surfaces,
observe human decisions,
execute actions safely,
and remember confirmed learning.
```

Tilo must not be positioned or implemented as a traditional SaaS product with AI features attached.

The public-facing product should feel simple. The framework internals should be powerful, documented, and inspectable.

---

## 2. Product Principle

```text
Simple surface. Powerful runtime. Inspectable internals.
```

This means:

- users see a focused AI-native experience;
- developers can inspect the runtime when needed;
- framework contracts are stable and documented;
- demo should not look like an admin dashboard;
- one polished example is better than many noisy examples;
- framework logic should live in runtime contracts, not in hand-wired UI panels.

---

## 3. v1.0 Goals

1. Redesign the public demo into a minimal AI-native experience.
2. Stabilize the core framework contracts.
3. Prove the ROAM loop end-to-end through tests.
4. Make app development reproducible and documented.
5. Improve release readiness: tests, CI, verification, docs.
6. Update README and launch assets for a v1.0 release.

---

## 4. P0: Minimal Public Demo

Implement the redesign in:

```text
docs/DEMO_SIMPLIFICATION_REDESIGN.md
```

Add:

```text
/demo
```

Keep `/demo/telegram` available for compatibility or internal debugging.

### Required behavior

The new `/demo` should show:

1. minimal centered input;
2. example chips;
3. focused result card;
4. primary actions;
5. optional drawers for explanation and trace.

Default flow:

```text
Submit contract review goal
-> focused contract review result
-> approve revision
-> revision draft result
-> optional memory prompt
```

### Hide by default

Do not show these in the default view:

- developer inspector;
- live event list;
- renderer decision;
- model diagnostics;
- interaction contract;
- durable observations;
- raw trace;
- JSON.

Expose them only through:

```text
Why this UI?
View trace
Developer mode
```

### Acceptance criteria

- `/demo` feels like a modern AI product.
- First-time users can understand it in 10 seconds.
- Runtime details are accessible but hidden by default.
- README points to `/demo` when stable.
- `/demo/telegram` remains available.

---

## 5. P0: End-to-end ROAM Contract

Target chain:

```text
User goal
-> ConversationMessageService
-> RunManager
-> ArtifactSpecV1
-> focused surface render
-> ArtifactActionRuntime
-> UIInteractionEvent
-> ConversationTurn(observation)
-> ContextReflectionService
-> Memory candidate
-> human confirmation
-> confirmed memory
```

### Required tests

Add or strengthen tests proving:

1. User message creates task, run, and artifact.
2. Artifact contains executable actions.
3. Action runtime executes selected action.
4. Action runtime creates UIInteractionEvent.
5. Action runtime appends observation turn with session id.
6. Context reflection can propose memory candidate.
7. Memory candidate is not confirmed automatically.
8. User confirmation confirms memory.
9. Prompt/context path can include recent turns and observations.
10. Deterministic mode passes without API key.

### Acceptance criteria

- One test covers the full chain from conversation message to action observation to memory candidate.
- Tests do not require external LLM calls.
- Test names clearly describe the framework contract.

---

## 6. P0: Framework Contract Stabilization

v1.0 should stabilize and document these public contracts:

### App Manifest

```text
app.yaml
```

Required fields:

- id;
- version;
- name;
- description;
- entry;
- runtime;
- surfaces;
- sample_inputs;
- tools;
- channels.

### Interaction Policy

```text
interaction.policy.yaml
```

Required decisions:

```text
no_ui
ask_text
mini_surface
rich_surface
```

### Artifact Spec

```text
artifact_spec.v1
```

Required fields:

- artifact_type;
- title;
- status;
- blocks;
- actions;
- provenance;
- memory_refs;
- run_id.

### Artifact Action Runtime

```text
POST /api/artifacts/{artifact_id}/actions/{action_id}
```

Required behavior:

- action resolution;
- action result;
- event creation;
- observation linkage;
- safe handling of unsupported actions.

### Conversation Runtime

Document and validate:

- ConversationSession;
- ConversationTurn;
- message endpoint;
- observation turns;
- rich surface link turns.

### Acceptance criteria

- Docs reflect actual code.
- Validation scripts catch common mistakes.
- README references only stable concepts.
- Old v0.x implementation details stay in implementation history.

---

## 7. P1: Developer Experience for Building Apps

Ensure this works:

```bash
python scripts/create_app.py my-agent
python scripts/validate_app.py examples/apps/my-agent
```

Update:

```text
docs/BUILD_YOUR_FIRST_TILO_APP.md
```

It should guide a developer through:

1. scaffold app;
2. edit manifest;
3. edit policy;
4. define surfaces;
5. add sample fixture;
6. validate app;
7. run demo locally;
8. inspect action runtime;
9. understand memory candidate lifecycle.

Keep example apps minimal:

```text
contract-review-agent
sales-followup-agent
```

Do not add more example apps before v1.0.

---

## 8. P1: Release Readiness

Ensure these commands are documented and pass where environment allows:

```bash
python -m pytest backend/tests
python scripts/validate_app.py examples/apps/contract-review-agent
python scripts/validate_app.py examples/apps/sales-followup-agent
bash scripts/verify_local_demo.sh
```

Frontend:

```bash
cd frontend
pnpm install
pnpm build
```

CI should run:

- backend tests;
- example app validation;
- frontend build.

Add:

```text
docs/RELEASE_V1_0.md
```

It should include:

- what Tilo is;
- what is stable in v1.0;
- what is experimental;
- quick start;
- known limitations;
- roadmap after v1.0.

---

## 9. P1: README and Launch Assets

Update README and Chinese README after `/demo` is stable.

Required changes:

- Quick Start points to `/demo`.
- `/demo/telegram` is described as legacy/internal if still kept.
- Add concise v1.0 positioning.
- Keep overview hero image.
- Add real screenshot only if captured from current UI.

Do not add fake screenshots.

---

## 10. P2: Optional Developer Mode

The new `/demo` can include a Developer Mode toggle.

Default off.

When enabled, show subtle access to:

- why this UI;
- action runtime result;
- observation event;
- memory candidate;
- trace.

Developer Mode should not turn the page into a dashboard.

---

## 11. Non-goals

Do not do these in v1.0:

- full workflow builder;
- full artifact editor;
- model marketplace;
- app marketplace;
- new channel adapters;
- new large demo scenario;
- heavy admin console.

v1.0 is framework foundation, not an enterprise platform.

---

## 12. Suggested Implementation Order

1. Add `/demo` minimal route using existing backend APIs.
2. Build focused contract review flow.
3. Add drawers for explanation and trace.
4. Wire actions through Artifact Action Runtime.
5. Add end-to-end ROAM contract tests.
6. Update docs for stable framework contracts.
7. Update Build Your First Tilo App guide.
8. Add release notes.
9. Update README after demo is stable.
10. Run tests and verification.

---

## 13. Definition of Done

v1.0 is done when:

1. `/demo` is the primary public demo.
2. Demo is minimal by default and hides framework internals.
3. Contract review flow works end-to-end.
4. Artifact actions execute through backend runtime.
5. Observations and memory candidates are created through the runtime loop.
6. Core framework contracts are documented and validated.
7. App scaffold and validation path works.
8. CI covers backend tests, app validation, and frontend build.
9. README and Chinese README are updated for v1.0.
10. Release notes document stable features and known limitations honestly.
