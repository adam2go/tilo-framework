# Implementation History

This file keeps a compact history of earlier planning docs so `docs/` stays readable for new contributors.

The active documentation should focus on:

- what Tilo is;
- how to run it;
- how the runtime works;
- how to build an app;
- what the next implementation milestone is.

Older audit notes, one-off demo plans, and Codex execution prompts were consolidated here instead of staying as many separate top-level docs.

---

## v0.2: Memory, Artifacts, and Self-improvement Foundation

The earliest v0.2 plans focused on strengthening the original framework loop:

```text
Conversation -> Task -> Run -> Memory Recall -> Skill Selection -> Tool Execution -> Artifact Generation -> Human Confirmation -> Memory Update
```

Main ideas:

- structured memory recall;
- memory candidate lifecycle;
- `artifact_spec.v1`;
- renderer registry;
- feedback and skill candidate primitives;
- run metrics and trace hardening;
- basic eval scaffolding.

Most of these ideas either became part of the current runtime or were superseded by the later ROAM direction.

---

## v0.4: Interaction Runtime Direction

The v0.4 planning shifted Tilo away from being a generic console and toward a reusable interaction runtime.

Key decisions:

- keep the experience conversation-first;
- show UI only when human decision-making needs structure;
- make user actions durable observations;
- introduce mini surfaces and rich surface escalation;
- avoid building a heavy dashboard.

This direction became the foundation for the current ROAM loop.

---

## ROAM Foundation

The ROAM implementation plan made the product spine explicit:

```text
Render -> Observe -> Act -> Memorize
```

Core decisions:

- UI is not only a display layer; it is part of the agent runtime.
- `UIInteractionEvent` records user actions.
- Artifact actions and state bindings connect UI components to backend state.
- Interaction components should be reusable, not demo-only.
- Important user actions should persist durable observations.

The current docs now cover this in:

- `docs/ROAM_LOOP.md`
- `docs/AI_NATIVE_INTERACTION_COMPONENTS.md`
- `docs/CONVERSATION_RUNTIME.md`
- `docs/MEMORY.md`

---

## Telegram-like Demo and LLM Integration

The Telegram-like demo plan introduced a public showcase route:

```text
/demo/telegram
```

Its purpose was to prove:

```text
Chat is the entry. Surface is the workspace. Interaction becomes memory.
```

The related LLM plan added OpenAI-compatible backend-only configuration, deterministic fallback, runtime capabilities, and a contract-review-specific generation path.

Current README now points directly to `/demo/telegram` as the main demo entry.

---

## Demo Polish Direction

The demo polish plan focused on making the public demo easier to understand:

- center surface should be the visual hero;
- left chat should feel alive;
- right inspector should explain, not dominate;
- deterministic fallback must always work;
- screenshots should reflect the real UI, not mockups.

This direction is carried forward into the next active milestone.

---

## Current Active Milestone

See:

```text
docs/V0_8_DEMO_RELIABILITY_AND_OPEN_SOURCE_DX_PLAN.md
docs/V0_8_CODEX_EXECUTION_PROMPT.md
```

v0.8 focuses on public demo reliability, documentation clarity, first-run developer experience, and release-ready validation.
