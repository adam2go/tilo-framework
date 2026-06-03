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
- `docs/AI_NATIVE_FRAMEWORK_PRINCIPLES.md`
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

The route is no longer a separate public demo. In v1.0, `/demo` is the primary public demo and `/demo/telegram` redirects there for compatibility. The backend Telegram channel adapter remains an experimental channel integration, but the large Telegram-like frontend showcase was removed.

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
docs/REFACTOR_BLUEPRINT.md          ← active engineering blueprint
docs/SURFACE_PROTOCOL.md            ← Phase 0 deliverable: protocol contract
```

The active work is the Surface Protocol & Streaming ROAM refactor: making
the product claim ("flexibly / instantly / goal-driven generated UI; full
ROAM closed loop") true in code, not just in docs. v1.0 is held until the
refactor's Definition of Done in `REFACTOR_BLUEPRINT.md` §10 is satisfied.

---

## Refactor: Surface Protocol & Streaming ROAM

Started under `docs/REFACTOR_BLUEPRINT.md`. Goal: make the product claim
("flexibly / instantly / goal-driven generated UI; full ROAM closed loop") true
in code, not just in docs.

### Phase 0 — Surface Protocol contract (landed)

- `docs/SURFACE_PROTOCOL.md` — normative `tilo.surface.v1` spec.
- `backend/app/schemas/surface.py` — Pydantic models (single source of truth).
- `scripts/export_surface_schema.py` — JSON Schema exporter (with `--check`).
- `frontend/lib/surface.schema.json` — generated JSON Schema for non-Python renderers.
- `backend/tests/test_surface_schema.py` — 33 tests covering all 10 normative
  validation rules, every intent, every block-type data shape, and JSON Schema
  drift.

No runtime code is wired to the new protocol yet (per ADR-8 backward-compat
window). Phases 1+ progressively migrate `InteractionPolicy`, `RunManager`,
the artifact/surface composer, and the frontend renderer.

### Phase 1 — `InteractionPolicy` returns intents; wired into `RunManager` (landed)

- `backend/app/services/interaction_policy/schemas.py` — `InteractionRule`
  now accepts both `intent:` (preferred, from the closed Surface Protocol
  vocabulary) and legacy `surface:` (auto-mapped to an intent through
  `LEGACY_SURFACE_TO_INTENT`). UI decisions without either field are
  rejected; `no_ui` / `ask_text` rules are forbidden from declaring
  either field.
- `backend/app/services/interaction_policy/service.py` — `evaluate(...)`
  emits both `intent` and (when source rule had it) the legacy `surface`
  on every UI decision. `validate_for_app(...)` validates intents against
  the new optional `surfaces.intents` manifest field, while preserving
  legacy surface-name validation.
- `backend/app/services/apps/schemas.py` — `AgentAppSurfaceConfig` gained
  an optional `intents: list[str]` field.
- `backend/app/services/agent_runtime/planner.py` — every plan step now
  carries `signal / risk_level / category / requires_user_decision`
  metadata so policy can be evaluated per step.
- `backend/app/services/agent_runtime/run_manager.py` — `RunManager.execute`
  now resolves the session's app, loads the `InteractionPolicy`, evaluates
  the policy for every plan step, persists the decisions on `Run.plan_json`,
  and records one `policy_decision` trace entry per step. Missing or
  malformed policies degrade gracefully to `no_ui`.
- `examples/apps/contract-review-agent/interaction.policy.yaml` and
  `examples/apps/sales-followup-agent/interaction.policy.yaml` migrated
  to dual-write `intent:` + `surface:` for backward compatibility.
- `backend/tests/test_policy_runtime_integration.py` — 14 new tests
  covering rule schema variants, intent emission, manifest validation
  for intent-only apps, planner metadata, and end-to-end `RunManager`
  behaviour (per-step decisions on plan, per-step trace entries,
  graceful fallback when the app id is unknown).

Total backend tests after Phase 1: **103 passed**, zero regressions.
`Run.plan_json["policy_decisions"]` is now a stable structured record of
"what would have happened to UI on each step", consumable by Phase 2's
`SurfaceComposer`.

### Phase 2 — Streaming `SurfaceTurn` + `SurfaceComposer` (landed)

This is the load-bearing phase: ROAM's "Render" step is now an actual
runtime artifact, not a frontend assumption.

- `backend/app/models/domain.py` — new `SurfaceTurn` table (run_id,
  session_id, ordinal, intent, surface_spec_json, policy_decision_json,
  artifact_id link, composer_mode). One run produces zero or more turns
  in order. `app/core/migrations.py` ensures the table exists on legacy
  Postgres deployments.
- `backend/app/services/surface/composer.py` — `DeterministicSurfaceComposer`
  produces a structurally-valid `SurfaceSpec` for every supported intent
  (request_approval, collect_input, present_result, offer_choices,
  confirm_memory, show_progress, escalate_to_rich, ask_clarification).
  `safe_compose(...)` wraps any composer with deterministic fallback
  on `ValidationError | ValueError | TypeError`, exactly per ADR-7.
- `backend/app/services/surface/persistence.py` — `SurfaceTurnService`
  persists a `ComposedSurface`, stamps the spec ids to the row id,
  appends a `ConversationTurn(turn_type=mini_surface | rich_surface_link)`
  with the SurfaceSpec as its `surface_payload_json`.
- `backend/app/services/agent_runtime/run_manager.py` — refactored to
  walk the plan once. Per step: evaluate `InteractionPolicy`, perform
  step side effects, and (when policy emits a UI decision and the step
  is surface-eligible) compose + persist a SurfaceTurn. Real-time UI
  budget counters now drive the next step's policy context. The Artifact
  pipeline is preserved — contract review still emits a structured
  Artifact, plus an `artifact_link` SurfaceTurn that points at it.
- `backend/app/api/routes/runs.py` — new `GET /api/runs/{run_id}/surface-turns`
  returns turns in ordinal order.
- `backend/app/api/routes/conversations.py` — new
  `GET /api/conversations/{session_id}/surface-turns` filters by session
  for the streaming-aware frontend.
- `backend/app/schemas/domain.py` — `SurfaceTurnRead` ORM model.
- `backend/tests/test_run_streaming.py` — 17 tests covering the
  deterministic composer per intent, `safe_compose` fallback,
  persistence, end-to-end RunManager streaming, backward-compat with
  the existing Artifact path, and both new HTTP endpoints.
- One existing test in `test_health_and_runtime.py` adjusted to expect
  the new `surface_turns` key in `RunManager.execute(...)`'s result.

Total backend tests after Phase 2: **120 passed**, zero functional
regressions. `Run.plan_json["surface_turn_ids"]` is the canonical handle
the frontend uses to retrieve the ordered surface stream for a run.

### Phase 3 — `<TiloRenderer>` consumes Surface Protocol (landed)

Surface-as-data lands on the frontend. The reference renderer is now
fully data-driven; **no per-app branching, no `artifact_type` switch**,
no renderer-specific names leaking into the runtime.

- `frontend/lib/surface.ts` — TypeScript types mirroring
  `tilo.surface.v1` (intents, block-type unions, action contract,
  `SurfaceTurn` row shape).
- `frontend/lib/surfaceClient.ts` — fetch helpers for the Phase 2
  endpoints (`/api/runs/{id}/surface-turns`, `/api/conversations/{id}/surface-turns`)
  and a unified `executeSurfaceAction` that routes through the existing
  artifact-action runtime when an artifact is bound, else records a
  generic `UIInteractionEvent`.
- `frontend/components/surface/blocks.tsx` — 12 default block
  components (Heading, Text, Evidence, Comparison, Decision, Form,
  Progress, List, Link, Editable, ArtifactLink, Fallback). Built on
  Tailwind, headless action firing through a `fire(actionId, payload?)`
  callback so blocks stay visual-only.
- `frontend/components/surface/TiloRenderer.tsx` — top-level renderer.
  Supports per-block override via the `components` prop:
  `<TiloRenderer surface={...} components={{ decision: MyDecision }} />`.
  Implements `block_compat: graceful` — unknown block types render
  their `fallback_text` instead of crashing the page.
- `frontend/components/surface/useTiloSurface.ts` — hook for loading
  the SurfaceTurn stream by run id or session id, with optional
  polling.
- `frontend/components/surface/index.ts` — single public entry point;
  internal modules (`./blocks`, `./types`) are implementation details.
- `frontend/app/demo/v2/page.tsx` — new demo route exercising the full
  pipeline end-to-end (create session → send goal → render the streamed
  SurfaceTurns through `<TiloRenderer>`). The pre-existing `/demo`
  remains untouched during the migration window per ADR-8.

The legacy renderers (`frontend/components/mini-surfaces/*` and
`frontend/components/interaction/registry.tsx`) are retained for the
existing `/demo` and `/workspace` routes; they will be removed in
Phase 6 once the new renderer becomes the default.

`tsc --noEmit` clean. Backend regression: **120 backend tests** still
pass; the JSON Schema export (`scripts/export_surface_schema.py --check`)
reports no drift.

### Cleanup landed alongside Phase 3

Six obsolete docs were removed (their content was superseded or never
referenced from running code):

- `docs/V1_0_CODEX_EXECUTION_PROMPT.md` — one-off Codex prompt.
- `docs/V1_0_FRAMEWORK_RELEASE_PLAN.md` — superseded by `REFACTOR_BLUEPRINT.md`.
- `docs/PRIORITY_ACTION_PLAN.md` — superseded by `REFACTOR_BLUEPRINT.md`.
- `docs/RELEASE_V1_0.md` — premature release notes; v1.0 now gated on
  `REFACTOR_BLUEPRINT.md` §10.
- `docs/MINI_SURFACE_REGISTRY.md` — superseded by `SURFACE_PROTOCOL.md`.
- `docs/DEMO_SCREENSHOTS.md` — placeholder guidance, no committed
  screenshots, no inbound references.

`docs/README.md`, the README links, and `REFACTOR_BLUEPRINT.md` were
updated to reflect the new layout.

### Phase 4 — Behaviour-aware Memory (landed)

UI behaviour is now first-class memory input. The memory extractor reads
the recent `UIInteractionEvent` stream and proposes typed candidates
that capture *behavioural* signal, not just artifact content.

- `backend/app/services/memory/behaviour.py` — new
  `BehaviourMemoryAnalyzer` with three deterministic rules:
  - `repeated_rejects` (≥ 3 rejects on the same `block_id` within a
    50-event window) → `preference_negative` candidate.
  - `repeated_selects` (≥ 2 selects of the same option value) →
    `preference_positive` candidate.
  - `editable_memory_updated` (an `editable` block whose
    `state_binding` points at a memory was edited) →
    `memory_update_proposed` candidate.

  Every candidate carries a `behaviour_signature` so subsequent runs
  de-dup against existing behaviour memories — no more emitting the
  same insight every run.

- `backend/app/services/memory/extraction.py` — `MemoryExtractionService`
  now accepts an optional `recent_interaction_events` argument; when
  not supplied it loads the last 50 events itself. Behaviour candidates
  are persisted as `source_type="ui_behaviour"` alongside the existing
  task-experience candidate. The `extract_memory` trace entry now
  enumerates the behaviour rules that fired, including each
  candidate's `behaviour_signature` and source rule.

- `backend/app/services/memory/writer.py` — `MemoryWriter.create_candidate`
  gained a `source_type` parameter (default `"run"`) so behaviour
  memories can be distinguished from task-experience memories.

- `backend/tests/test_behaviour_memory.py` — 8 tests covering all three
  rules, threshold boundaries, signature dedup, end-to-end persistence
  with the existing task-experience candidate, full HTTP round-trip
  via `/api/conversations/{id}/messages` + `/api/memories`, and the
  no-double-emit invariant across consecutive runs.

`RunManager` itself is unchanged — Phase 4 is a transparent extension
of `MemoryExtractionService`. Backend regression: **128 passed**, zero
existing tests broken, zero new lint findings.

The memory-recall pipeline (Phase 1 of an earlier round) already
includes confirmed memories in the prompt, so once a user confirms a
behaviour candidate it surfaces in subsequent runs without further
plumbing.

#### Phase 4 follow-up — action-stream signal, UI-decoupled

The first cut of the analyzer keyed `preference_negative` candidates by
`block_id`. That conflated *what the user did* with *which UI control
showed it*. The follow-up changes the signal model:

- **Signature is operation-based, not UI-based.** Repeated rejects
  group by `(operation, risk_level, category)` extracted from the
  rejection action's payload, so three rejects of the same kind of
  decision register as one behavioural pattern even when shown via
  three different surfaces. Block ids are kept inside
  `structured_payload.block_ids_seen` for audit only.
- **Rule renamed.** The third rule's `behaviour_signature` becomes
  `memory_edit:{memory_id}` and the rule key becomes
  `memory_edit_proposed`. Edit semantics, not editable-block
  implementation.
- **Rejects without an `operation` are skipped** entirely instead of
  being lumped under a synthetic key.

The framework now learns from the user's action stream, not the
particular UI element that surfaced the decision. **9 tests** pass.

### Phase 6 — Embedded demo + landing rework + local dev script (landed)

The product surface catches up to the framework. Two new demo routes
showcase the Surface Protocol end-to-end, and a single-command local
runner unblocks the "show me how it looks" moment.

- `frontend/app/demo/v2/page.tsx` — the headline Surface Protocol
  demo. Reworked into a clean Tailwind page with three sample-goal
  buttons (Contract Review, Sales Follow-up, Competitive Analysis),
  inline run-trace and memory drawers, and a streaming list of
  `SurfaceTurn`s rendered through `<TiloRenderer>`. No per-app
  branching anywhere in the page code — the agent picks intents and
  blocks, the page renders whatever comes back.

- `frontend/app/demo/embedded/page.tsx` — new embedded demo. A
  deliberately bland fake CRM ("ContractRoom CRM") with Tilo as a
  floating bottom-right panel. Demonstrates the host-product story:
  the host owns the page, Tilo only owns the panel and its surfaces.
  Same backend, same protocol, same `<TiloRenderer>`.

- `frontend/app/page.tsx` — landing page reworked to lead with the
  Surface Protocol demo and the embedded demo; the legacy `/demo`,
  `/workspace?demo=sales`, and `/workspace?demo=competitive` are kept
  as "legacy" cards during the migration window.

- `.env.local.example` — minimal local-dev defaults (SQLite, no LLM
  key, frontend points at `http://localhost:8000`).

- `scripts/dev.sh` — single-command local runner. Bootstraps a Python
  venv on first use, installs only runtime deps, copies
  `.env.local.example → .env` if needed, and starts uvicorn (:8000)
  + Next.js (:3000). Supports `--backend-only` / `--frontend-only`.
  Verified end-to-end on macOS: backend ready in ~12s, contract-review
  goal produces 2 SurfaceTurns (request_approval mini → confirm_memory
  mini), all via deterministic composer with no API key.

The legacy `/demo` route and the `frontend/components/mini-surfaces/`
+ `interaction/registry.tsx` modules are intentionally **not** removed
yet — they back routes that are still linked from the landing page as
"legacy" cards. They will be removed in a follow-up commit once the
new routes are battle-tested.

After Phase 6: **129 backend tests** pass, frontend `tsc --noEmit`
clean, JSON-Schema export `--check` reports no drift.
