# Tilo Documentation

This folder is organized for contributors who want to understand, run, or extend Tilo quickly.

Start with the README first. Use this page when you need deeper implementation references.

---

## Start Here

- [`../README.md`](../README.md) — project overview, quick start, examples, roadmap.
- [`../README.zh-CN.md`](../README.zh-CN.md) — Chinese README.
- [`USER_GUIDE.md`](./USER_GUIDE.md) — using the current demo and console.
- [`BUILD_YOUR_FIRST_TILO_APP.md`](./BUILD_YOUR_FIRST_TILO_APP.md) — build a new declarative Tilo app.
- [`DEMO_SCREENSHOTS.md`](./DEMO_SCREENSHOTS.md) — capture real screenshots from the running demo.

---

## Core Concepts

- [`ROAM_LOOP.md`](./ROAM_LOOP.md) — the main product loop: Render -> Observe -> Act -> Memorize.
- [`AI_NATIVE_INTERACTION_COMPONENTS.md`](./AI_NATIVE_INTERACTION_COMPONENTS.md) — how agent-generated UI components work.
- [`INTERACTION_MINIMALISM_AND_AGENT_AUTONOMY.md`](./INTERACTION_MINIMALISM_AND_AGENT_AUTONOMY.md) — why Tilo should stay agent-first and UI-light.
- [`CHANNEL_AND_SURFACE_STRATEGY.md`](./CHANNEL_AND_SURFACE_STRATEGY.md) — how surfaces map across web, Telegram, and future channels.

---

## Runtime References

- [`APP_MANIFEST.md`](./APP_MANIFEST.md) — app manifest shape and loading behavior.
- [`INTERACTION_POLICY.md`](./INTERACTION_POLICY.md) — when the runtime should show no UI, mini UI, rich UI, or ask text.
- [`MINI_SURFACE_REGISTRY.md`](./MINI_SURFACE_REGISTRY.md) — inline mini surface registration and rendering.
- [`CONVERSATION_RUNTIME.md`](./CONVERSATION_RUNTIME.md) — conversation sessions, turns, messages, and observation linkage.
- [`ARTIFACT_ACTION_RUNTIME.md`](./ARTIFACT_ACTION_RUNTIME.md) — unified backend execution path for artifact actions.
- [`ORID_CONTEXT_REFLECTION.md`](./ORID_CONTEXT_REFLECTION.md) — deterministic reflection for explainable memory candidates.
- [`MEMORY.md`](./MEMORY.md) — memory lifecycle and recall design.
- [`ARTIFACTS.md`](./ARTIFACTS.md) — artifact spec and renderable output protocol.
- [`SKILLS.md`](./SKILLS.md) — reusable skill primitives.
- [`API_CONTRACTS.md`](./API_CONTRACTS.md) — backend API contracts.

---

## Engineering Rules

- [`PROJECT_CONSTITUTION.md`](./PROJECT_CONSTITUTION.md) — highest-level project constraints.
- [`QUALITY_BAR.md`](./QUALITY_BAR.md) — quality expectations for implementation.
- [`IMPLEMENTATION_RULES.md`](./IMPLEMENTATION_RULES.md) — coding and architecture rules.
- [`DEVELOPMENT_WORKFLOW.md`](./DEVELOPMENT_WORKFLOW.md) — local development workflow.

---

## Active Plan

- [`V0_9_ARTIFACT_ACTION_RUNTIME_PLAN.md`](./V0_9_ARTIFACT_ACTION_RUNTIME_PLAN.md) — next implementation milestone.
- [`V0_9_CODEX_EXECUTION_PROMPT.md`](./V0_9_CODEX_EXECUTION_PROMPT.md) — copy-paste prompt for Codex.

---

## History

- [`IMPLEMENTATION_HISTORY.md`](./IMPLEMENTATION_HISTORY.md) — compact history of older implementation plans.

Older one-off roadmap and Codex prompt files were consolidated into `IMPLEMENTATION_HISTORY.md` so this folder stays useful for new contributors.
