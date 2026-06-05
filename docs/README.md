# Tilo Documentation

This folder is organized for contributors who want to understand, run, integrate, or extend Tilo quickly.

Start with the README first. Use this page when you need deeper implementation references.

---

## Start Here

- [`../README.md`](../README.md) — project overview, quick start, examples, roadmap.
- [`../README.zh-CN.md`](../README.zh-CN.md) — Chinese README.
- [`tutorials/quickstart.md`](./tutorials/quickstart.md) — **5-minute quickstart** (pip install → rendered surface).
- [`GENERATE.md`](./GENERATE.md) — **generate & render reference**: `tilo.generate()`, `AIPPromptBuilder`, skills, `tilo.view()`.
- [`INTEGRATION_GUIDE.md`](./INTEGRATION_GUIDE.md) — integrate Tilo into an existing product.
- [`USER_GUIDE.md`](./USER_GUIDE.md) — using the current demo and console.
- [`BUILD_YOUR_FIRST_TILO_APP.md`](./BUILD_YOUR_FIRST_TILO_APP.md) — build a new declarative Tilo app.

---

## Core Concepts

- [`ROAM_LOOP.md`](./ROAM_LOOP.md) — the main product loop: Render → Observe → Act → Memorize.
- [`AI_NATIVE_FRAMEWORK_PRINCIPLES.md`](./AI_NATIVE_FRAMEWORK_PRINCIPLES.md) — positioning constraints for an AI-native product runtime framework.
- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — backend and frontend runtime boundaries.
- [`REFACTOR_BLUEPRINT.md`](./REFACTOR_BLUEPRINT.md) — architecture decision records (8 ADRs) behind the surface protocol.

---

## Runtime References

- [`SURFACE_PROTOCOL.md`](./SURFACE_PROTOCOL.md) — surface protocol (preferred reference for new code).
- [`APP_MANIFEST.md`](./APP_MANIFEST.md) — app manifest shape and loading behavior.
- [`INTERACTION_POLICY.md`](./INTERACTION_POLICY.md) — when the runtime should show no UI, mini UI, rich UI, or ask text.
- [`CONVERSATION_RUNTIME.md`](./CONVERSATION_RUNTIME.md) — conversation sessions, turns, messages, and observation linkage.
- [`ARTIFACT_ACTION_RUNTIME.md`](./ARTIFACT_ACTION_RUNTIME.md) — unified backend execution path for artifact actions.
- [`ORID_CONTEXT_REFLECTION.md`](./ORID_CONTEXT_REFLECTION.md) — deterministic reflection for explainable memory candidates.
- [`MEMORY.md`](./MEMORY.md) — memory lifecycle and recall design.
- [`ARTIFACTS.md`](./ARTIFACTS.md) — artifact spec and renderable output protocol (legacy `artifact_spec.v1`; coexists with surface protocol during refactor per ADR-8).
- [`SKILLS.md`](./SKILLS.md) — reusable skill primitives.
- [`SKILL_TOOL_MCP_BOUNDARIES.md`](./SKILL_TOOL_MCP_BOUNDARIES.md) — Skill, Tool, and MCP ownership boundaries.
- [`API_CONTRACTS.md`](./API_CONTRACTS.md) — backend API contracts.
- [`../evals/baseline_report.md`](../evals/baseline_report.md) — deterministic baseline runtime metrics.

---

## Engineering Rules

- [`PROJECT_CONSTITUTION.md`](./PROJECT_CONSTITUTION.md) — highest-level project constraints.
- [`QUALITY_BAR.md`](./QUALITY_BAR.md) — quality expectations for implementation.
- [`IMPLEMENTATION_RULES.md`](./IMPLEMENTATION_RULES.md) — coding and architecture rules.
- [`DEVELOPMENT_WORKFLOW.md`](./DEVELOPMENT_WORKFLOW.md) — local development workflow.
- [`SECURITY.md`](./SECURITY.md) — security posture.
