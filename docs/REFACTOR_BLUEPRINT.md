# Tilo Refactor Blueprint — Surface Protocol & Streaming ROAM

> Status: **Active**, owner: framework core
> Supersedes ad-hoc decisions previously scattered across `ARCHITECTURE.md`, `ROAM_LOOP.md`, `MINI_SURFACE_REGISTRY.md`, `INTEGRATION_GUIDE.md`.
> All future code changes during this refactor MUST cite a phase number from this document.

---

## 0. Why we are refactoring

Tilo's stated product goal:

> Reference ReAct, but pull **frontend UI interaction into the loop** so that interaction with humans becomes "**flexibly generated, instantly generated, goal-driven generated**" — the full ROAM loop (Render → Observe → Act → Memorize) replaces traditional pre-baked SaaS pages.

The current implementation only partially reflects this:

| Goal claim | Current reality | Gap |
|---|---|---|
| Goal-driven generated UI | `ArtifactSpecBuilder` is a hardcoded `if/elif` over 4 fixed `artifact_type`s with embedded fixture content | Not generated, not goal-driven |
| Render is part of the loop | Frontend always renders the full artifact; `InteractionPolicy` has 4 decision types but is **never called from `RunManager`** | Render decisions don't actually happen at runtime |
| Surface is composable | `mini-surface` is a registry of named React components; YAML policy says `surface: MiniIssueCard` | Surface is bound to a specific React implementation; cannot reach Vue / Slack / Telegram / email |
| One run = one focused decision | `RunManager.execute` produces one artifact with 5 blocks at once | Dashboard mindset, not ROAM |
| Easy integration | Frontend `npm` packages don't exist; backend isn't a `pip` package; integrating means forking | Integration requires a fork |
| Memory learns from UI behaviour | `MemoryExtractionService` ignores `UIInteractionEvent` records | UI behaviour is observed but never feeds back into memory |

The refactor below is the minimum set of changes that makes the product claim true.

---

## 1. Architectural decisions (ADRs)

These decisions are **binding** for the whole refactor. Anything that conflicts with one of them must change one of these decisions first.

### ADR-1 · Surface as Data, not Surface as Component
The runtime emits **structured surface data** describing intent and content. Renderers (React, Vue, Telegram, Slack, email) are downstream consumers. The runtime never references a renderer-specific component name.

Concretely:
- `interaction.policy.yaml` outputs `intent: request_approval`, **not** `surface: MiniApprovalCard`.
- The artifact / surface schema vocabulary is closed (fixed block types) and channel-agnostic.

### ADR-2 · Render layer and OAM layer are decoupled artifacts
We ship the project as multiple independent units:
- `tilo-runtime` (Python/FastAPI) — runtime, persistence, action semantics, memory. **No UI dependency.**
- `tilo-surface-protocol` — pure JSON Schema + auto-generated TypeScript types + Python types. **No framework dependency.**
- `tilo-react` — *one* reference renderer. Optional. Other renderers can exist.

Users adopting Tilo should be able to use any of these in isolation.

### ADR-3 · `intent` is the policy output; block vocabulary is the protocol output
- `InteractionPolicy.evaluate` returns one of: `no_ui` / `ask_text` / `mini_surface(intent)` / `rich_surface(intent)`.
- A `SurfaceComposer` translates `(intent, context)` → a concrete `SurfaceSpec` made of protocol blocks.
- Frontend never receives an "intent" alone; it always receives a fully composed `SurfaceSpec`. Intent is a *backend-internal* concept that travels through trace.

### ADR-4 · One Run produces a stream of `SurfaceTurn`s, not one Artifact
A `Run` is a logical unit of agent work. During a Run the agent produces zero or more `SurfaceTurn`s in order. Each `SurfaceTurn` is an atomic R→O→A iteration:
- the agent **renders** one focused surface,
- the user (or environment) **observes/acts**,
- the agent decides whether to render another surface, finish, or wait.

A long-form Artifact (e.g. a contract review document) becomes one *type* of SurfaceTurn payload referenced by `surface.kind = "rich"`. The `Artifact` table is retained for durable rich content but is no longer the *unit of run output*.

### ADR-5 · UI behaviour is first-class memory input
`MemoryExtractionService` consumes `UIInteractionEvent`s alongside artifact content. Repeated rejections, edits, and selections become typed behaviour-memory candidates with explicit provenance.

### ADR-6 · Defaults bias toward "less UI"
Per `INTERACTION_POLICY.md`, default policies prefer `no_ui` > `ask_text` > `mini_surface` > `rich_surface`. Apps must explicitly opt into heavier surfaces. This rule is encoded both in the default policy budget and in policy validation (warn when a policy has zero `no_ui` / `ask_text` rules).

### ADR-7 · LLM composition is guarded; deterministic always works
- `SurfaceComposer` may use an LLM to fill block content given an intent and context.
- Output is validated against the Surface Protocol JSON Schema.
- On any validation failure, fall back to a deterministic composer that produces a structurally-valid degraded surface (typically `intent + heading + fallback text`).
- Tests run end-to-end in deterministic mode with **no API key**.

### ADR-8 · Backward compatibility window
During the refactor we keep `artifact_spec.v1` readable and continue to emit it for existing callers. New endpoints emit `surface_spec.v1`. The two coexist for one minor version, then `artifact_spec.v1` is frozen and removed.

---

## 2. Target architecture

```
                      ┌─────────────────────────┐
   user message ───►  │   ConversationMessage   │
                      └────────────┬────────────┘
                                   ▼
                        ┌────────────────────┐
                        │     RunManager     │
                        │  (streaming loop)  │
                        └─────────┬──────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
        ┌──────────┐       ┌─────────────┐      ┌────────────┐
        │ Planner  │       │ Memory      │      │   Tools    │
        │  steps   │       │ (recall+    │      │ (executor) │
        │          │       │  behaviour) │      │            │
        └────┬─────┘       └─────────────┘      └─────┬──────┘
             │                                         │
             ▼                                         │
   ┌───────────────────────┐                           │
   │ InteractionPolicy     │  ← evaluates each step    │
   │ → no_ui | ask_text |  │                           │
   │   mini(intent) |      │                           │
   │   rich(intent)        │                           │
   └──────────┬────────────┘                           │
              │                                        │
              ▼                                        │
   ┌──────────────────────────────────────────────┐    │
   │                SurfaceComposer               │    │
   │ (intent, context, block catalog) → SurfaceSpec│   │
   │      validate against JSON Schema            │◄───┘
   │      fallback to deterministic on failure    │
   └────────────────────┬─────────────────────────┘
                        │
                        ▼
              ┌───────────────────┐
              │  SurfaceTurn      │  (persisted, ordered, per-Run)
              │   = one R-step    │
              └─────────┬─────────┘
                        │  emitted to channel(s) / SSE
                        ▼
              ┌───────────────────┐         ┌──────────────────────┐
              │  Channel renders  │ ──────► │ UIInteractionEvent   │
              │  block-by-block   │  user   │  ConversationTurn    │
              │  (React/Vue/TG..) │ action  │  (observation)       │
              └───────────────────┘         └──────────┬───────────┘
                                                       │
                              (reflect, optional)      ▼
                                              ┌────────────────┐
                                              │  RunManager    │
                                              │  decides next  │
                                              │  SurfaceTurn   │
                                              └────────────────┘
```

ROAM mapping:

- **R**ender = `SurfaceComposer` → `SurfaceTurn`
- **O**bserve = `UIInteractionEvent` + `ConversationTurn(observation)`
- **A**ct = `ArtifactActionRuntime` (existing, stays)
- **M**emorize = `MemoryExtractionService` (extended to consume `UIInteractionEvent`s)

---

## 3. Surface Protocol v1 (overview)

Authoritative definition lives in `docs/SURFACE_PROTOCOL.md` (Phase 0 deliverable).

### Top-level `SurfaceSpec`

```jsonc
{
  "schema_version": "tilo.surface.v1",
  "surface_id": "<uuid>",
  "intent": "request_approval",        // closed vocabulary, see below
  "budget_hint": "mini" | "rich",
  "blocks": [ /* ordered Block[] */ ],
  "fallback_text": "...",              // REQUIRED — used when no block is rendered
  "fallbacks": {                       // OPTIONAL — channel hints
    "telegram": { "inline_keyboard": [...] },
    "slack":    { "blocks": [...] },
    "email":    { "html": "..." }
  },
  "block_compat": "graceful",          // graceful | strict
  "provenance": [...],
  "memory_refs": [...],
  "run_id": "...",
  "turn_id": "..."                     // links to SurfaceTurn
}
```

### Closed `intent` vocabulary (v1)

```
request_approval        – binary or small-N decision needed to continue
collect_input           – structured fields needed before agent can proceed
present_result          – read-only result for the user to consume
offer_choices           – pick one of N alternatives
confirm_memory          – ask user whether to remember a fact / preference
show_progress           – long-running progress / status
escalate_to_rich        – inline summary that links to a rich artifact
ask_clarification       – open-ended text follow-up
```

### Closed block vocabulary (v1)

| type | purpose |
|---|---|
| `heading` | short title with optional severity |
| `text` | plain prose, supports inline emphasis only |
| `evidence` | quoted excerpt + source ref |
| `comparison` | left/right or table-shaped delta |
| `decision` | 1..N options with action_id and value |
| `form` | field set with validation hints |
| `progress` | step list / percentage / status |
| `list` | bullet or ordered items |
| `link` | label + url + target (drawer/page/webview) |
| `editable` | rich-text or structured editable region (wraps content blocks) |
| `artifact_link` | reference to a full Artifact (mini → rich path) |
| `fallback` | last-resort text-only block, always renderable |

Each block carries:
```jsonc
{
  "id": "...",
  "type": "decision",
  "data": { /* type-specific shape */ },
  "fallback_text": "...",         // REQUIRED at block level too
  "actions": [ /* ArtifactAction[] — same as today */ ],
  "state_binding": { /* unchanged */ }
}
```

### Action contract
`ArtifactAction` (v1) is **unchanged**. The existing action types continue to apply: `approve|reject|edit|select|continue_task|regenerate|invoke_tool|create_memory|promote_skill|export|confirm`. This is the deliberate stability anchor.

### Versioning
- `schema_version` is required.
- Renderers receiving an unknown block type with `block_compat=graceful` MUST render the block's `fallback_text` and emit no error.
- Renderers receiving `block_compat=strict` MUST refuse and emit `surface.render_failed` interaction event.

---

## 4. Phase plan

Phases are *logical*, not time-boxed. Each phase has a **Done When** checklist that must be green before the next phase merges. Phases are designed so that the existing `/demo` keeps passing the `bash scripts/verify_local_demo.sh` check at every phase boundary.

### Phase 0 — Surface Protocol document & schemas

**Goal:** lock the contract before changing any code path.

Deliverables:
- `docs/SURFACE_PROTOCOL.md` — full normative spec (intents, blocks, versioning, fallbacks, design philosophy).
- `backend/app/schemas/surface.py` — Pydantic v2 models for `SurfaceSpec`, `SurfaceBlock`, `SurfaceIntent` enum, with strict validators.
- JSON Schema export: `tools/export_surface_schema.py` writes `frontend/lib/surface.schema.json`.
- Update `INTERACTION_POLICY.md` "design philosophy" section: prefer less UI; default ladder.

**Done When:**
- `pytest backend/tests/test_surface_schema.py` passes (round-trip validation for sample fixtures, one per intent).
- `python tools/export_surface_schema.py --check` succeeds with no diff.
- Existing `verify_local_demo.sh` still green.

### Phase 1 — `InteractionPolicy` returns intents; wire it into `RunManager`

**Goal:** make policy decisions actually happen during a run.

Changes:
- `InteractionRule.surface: str | None` becomes `InteractionRule.intent: SurfaceIntent | None`. Validation against `app.yaml.surfaces` is replaced with intent-level validation.
- `app.yaml.surfaces` becomes a hint to renderers, no longer authoritative for policy.
- `Planner` augments each step with `signal / risk_level / category / requires_user_decision`.
- `RunManager.execute` calls `InteractionPolicyService.evaluate` per step. Decision becomes the input to `SurfaceComposer`.
- Migrate `examples/apps/contract-review-agent/interaction.policy.yaml` and `sales-followup-agent` from `surface:` to `intent:`. Keep `surface:` accepted as deprecated alias for one minor version.

**Done When:**
- Trace shows a `policy_decision` step per `Planner` step.
- `examples/apps/*/interaction.policy.yaml` validate under both old and new shape.
- `pytest backend/tests/test_apps_and_policy.py` plus a new `test_policy_runtime_integration.py` pass.
- `verify_local_demo.sh` still green.

### Phase 2 — `SurfaceComposer` + streaming `SurfaceTurn`

**Goal:** turn one Run into a stream of focused, validated surfaces.

Changes:
- New table `surface_turns` (id, run_id, ordinal, intent, surface_spec_json, status, created_at). Migrations via `app/core/migrations.py`.
- New service `SurfaceComposer` with two backends:
  - `DeterministicSurfaceComposer` (always available, used as fallback);
  - `LLMSurfaceComposer` (used when `Settings.llm_enabled` and credentials exist).
- `SurfaceComposer.compose(intent, context) -> SurfaceSpec`, output validated by `SurfaceSpec` Pydantic model. On any failure → deterministic.
- `RunManager.execute` becomes `RunManager.run_loop`:
  - iterates over plan steps;
  - for each step, evaluates policy and (when not `no_ui`) calls composer;
  - persists `SurfaceTurn`;
  - appends a `ConversationTurn(turn_type="agent_surface")` referring to the SurfaceTurn;
  - emits SSE event on `/api/conversations/{session_id}/events` (new endpoint, additive).
- Existing `Artifact` is now produced **only** when intent is `escalate_to_rich` or when an app explicitly requests one. This collapses the `contract_review` 5-block dump into:
  1. `present_result` mini surface (risk summary + open-rich link), then
  2. on user open → rich artifact via existing `Artifact` path.
- `ConversationMessageService.send_message` returns the first SurfaceTurn synchronously and the rest stream over SSE.

**Done When:**
- `Run.surface_turns` is populated for all three example apps.
- Contract review demo emits **at least 2** SurfaceTurns: a focused approval mini, then on click a rich artifact link.
- `pytest backend/tests/test_run_streaming.py` covers: deterministic composer, LLM composer with mocked client, schema-failure fallback.
- Backward-compatible: `GET /api/artifacts?task_id=...` still returns the rich artifact when produced.

### Phase 3 — Frontend: `<TiloRenderer>` driven by Surface Protocol

**Goal:** make the reference UI render *blocks*, not *artifact_type*. Provide override hooks.

Changes:
- `frontend/lib/surface.ts` — TS types generated from JSON Schema (`pnpm gen:surface`).
- `frontend/components/surface/` — new directory:
  - `TiloRenderer.tsx` — top-level, takes `SurfaceSpec` + optional `components` override map.
  - `blocks/` — one component per block type (`Heading`, `Text`, `Evidence`, `Comparison`, `Decision`, `Form`, `Progress`, `List`, `Link`, `Editable`, `ArtifactLink`, `Fallback`). Each is **headless-ready**: state via `useTiloAction`, visuals via Tailwind/shadcn defaults.
  - `useTiloSurface.ts`, `useTiloAction.ts` — hooks.
- Old `mini-surfaces/*` and `interaction/registry.tsx` become **adapters** that wrap `<TiloRenderer>` to keep old call sites working during the transition.
- `Console.tsx` and `WorkflowSurface.tsx` consume SSE stream; render each `SurfaceTurn` as it arrives.
- Conversation flow renders the unified ladder: text bubble | mini surface card | rich artifact link.

**Done When:**
- `/demo` renders entirely via `<TiloRenderer>` (no direct calls to old block renderers).
- Users can pass `components={{ decision: MyDecision }}` to override one block; other blocks fall back to defaults.
- Removing `frontend/components/mini-surfaces/registry.ts` does not break compilation (it becomes a thin re-export).
- Visual baseline preserves the look of the current `/demo` page within reasonable tolerance (no committed screenshot baseline; verified by reviewer eyeball during merge).

### Phase 4 — Behaviour-aware Memory

**Goal:** UI interactions feed the memory candidate pipeline.

Changes:
- `MemoryExtractionService.extract_candidates` accepts a `recent_interaction_events: list[UIInteractionEvent]` argument.
- Add behaviour rules (initial set, deterministic):
  - 3 rejects on the same `block_id` within a run → memory candidate `{type: "preference_negative", content: "<derived>"}`.
  - 2 selects of the same option_value across runs → `{type: "preference_positive", ...}`.
  - 1 edit of an `editable` block whose binding is a memory → propose memory update.
- New `MemoryCandidate.source_type = "ui_behaviour"` recorded.
- These candidates surface through the existing `confirm_memory` intent — no new UI primitive.

**Done When:**
- Integration test simulates 3 rejects → asserts a `ui_behaviour` candidate appears.
- Confirmed `ui_behaviour` memories are recalled in the next run's prompt and shown in trace.

### Phase 5 — Packaging

**Goal:** make the "easy to integrate" claim physically true.

Changes:
- Backend:
  - `backend/pyproject.toml` becomes publishable as `tilo-runtime` package.
  - Default DB switches to SQLite (`tilo.db`); Postgres remains an opt-in config.
  - `tilo` CLI: `tilo init <name>`, `tilo serve`, `tilo validate`.
  - `create_tilo_router(config)` factory so users can mount Tilo into their existing FastAPI app.
- Frontend:
  - `pnpm` workspace; extract:
    - `packages/tilo-surface-protocol` (TS types + JSON schema, **no React**).
    - `packages/tilo-client` (fetch wrapper + SSE client; no React).
    - `packages/tilo-react` (renderer + hooks; default block components).
  - The existing `frontend/` Next.js app consumes these packages.
- Update `INTEGRATION_GUIDE.md` with three minimal recipes:
  1. React project: import `<TiloRenderer>`.
  2. Vue project: implement 11 block components, reuse `tilo-client`.
  3. Bare HTML / server-rendered: render `fallback_text` only.

**Done When:**
- `pip install tilo-runtime && tilo init demo && tilo serve` works on a clean machine.
- `pnpm create tilo-app` scaffolds a working React example consuming the local backend.
- A small Vue PoC under `examples/integrations/vue/` renders contract review with no Tilo React code.

### Phase 6 — Cowork demo on Surface Protocol & migration cleanup

**Goal:** make the canonical `/demo` route ride entirely on `<TiloRenderer>` + the SurfaceTurn stream, and clean up the renderers that pre-dated the Surface Protocol.

Changes (landed):
- `/demo` rewritten as `CoworkSurfaceDemo`: cowork-style left/right layout (conversation + summary panel + drawers) backed by the `SurfaceTurn` stream and `<TiloRenderer>`. No per-app branching anywhere in the page code.
- Legacy renderers removed: `frontend/components/ArtifactRenderer.tsx`, `frontend/components/Console.tsx`, `frontend/components/roam/`, `frontend/components/interaction/`, `frontend/components/mini-surfaces/`, `frontend/lib/miniSurfaceRegistry.ts`, `frontend/components/demo-minimal/MinimalDemoPage.tsx`.
- Legacy demo routes removed: `/demo/v2`, `/demo/embedded`, `/demo/telegram`, `/workspace`.
- `frontend/components/artifact/ArtifactDetail.tsx` rewritten as a minimal inspection page (no longer renders blocks itself; links back to the surface-turn stream and trace).
- Landing page (`/`) reduced to a single `Open Demo` CTA + GitHub.

Pending follow-ups (kept for a later commit, not blocking):
- Remove deprecated `surface:` alias in policy YAML once external apps have migrated.
- Remove the legacy `ArtifactSpecBuilder` hardcoded branches; only the rich-artifact path remains, and it should also be surface-spec-shaped end-to-end.
- Freeze `artifact_spec.v1`; document migration to `surface_spec.v1` in `docs/IMPLEMENTATION_HISTORY.md`.

**Done When:**
- `/demo` is the only demo route and renders entirely through `<TiloRenderer>` over the SurfaceTurn stream. ✅
- The frontend has no imports of `ArtifactRenderer`, `mini-surfaces/`, or `interaction/registry`. ✅
- `tsc --noEmit` clean and backend tests still green. ✅

---

## 5. Non-goals during this refactor

To prevent scope creep:

- No multi-agent orchestration changes.
- No new tool implementations (mock tools only).
- No real outbound side effects (email, Slack send) beyond what already exists.
- No auth / RBAC changes.
- No design system overhaul beyond the default block components.
- No change to `ArtifactAction` action_type vocabulary.

---

## 6. Risk register

| Risk | Mitigation |
|---|---|
| LLM produces invalid `SurfaceSpec` | Strict pydantic validation + deterministic fallback. ADR-7. |
| Renderers desync with new block types | `block_compat=graceful` + per-block `fallback_text`. |
| Streaming breaks existing single-shot consumers | `/api/conversations/{id}/messages` still returns first surface synchronously; SSE is additive. |
| Tests rot during big change | Each phase ships its own `pytest` file; CI runs `verify_local_demo.sh` per phase. |
| YAML breakage in user apps | Keep `surface:` as alias for one minor version (Phase 1 → Phase 6). |
| LLM cost in CI | LLM composer is off by default; tests use mocked `ModelClient`. |

---

## 7. Quality bar (applies to every phase)

- All new modules have type hints and Pydantic validation at IO boundaries.
- All new endpoints are additive until Phase 6.
- Every phase ships at least one targeted test file.
- `bash scripts/verify_local_demo.sh` MUST pass at the end of each phase.
- No secret in code, fixtures, traces, or logs (existing rule).
- Documentation in `docs/` updated *in the same commit* that introduces a behaviour change.

---

## 8. Traceability

Each phase corresponds to a top-level commit (or merge group). Commit messages MUST start with `refactor(surface-proto/phase-N): ...`. Phases-to-files index lives in `docs/IMPLEMENTATION_HISTORY.md` and is appended to as work lands.

---

## 9. Open questions (to resolve before Phase 5)

1. Do we ship `tilo-runtime` and `tilo-react` from the same repo (mono-repo) or split?
   - Default plan: mono-repo with workspace-level publishing scripts.
2. Do we keep Next.js as the reference UI shell or move to Vite + React?
   - Default plan: keep Next.js for now (existing demo works), evaluate after Phase 5.
3. Should `SurfaceTurn` be observable via WebSocket as well as SSE?
   - Default plan: SSE first; WebSocket later if a channel needs it.

These do not block Phases 0-4.

---

## 10. Definition of Done for the whole refactor

The refactor is complete when **all** of the following are true:

1. `interaction.policy.yaml` files in all example apps reference only `intent:`.
2. `RunManager` emits a stream of `SurfaceTurn`s; no run produces a 5-block monolith.
3. `<TiloRenderer>` renders any valid `SurfaceSpec` with no per-app branching.
4. A non-React renderer (Vue PoC) renders the contract review surfaces using only `tilo-client` + `tilo-surface-protocol`.
5. Memory candidates can originate from UI behaviour and feed back into prompts.
6. `pip install tilo-runtime` produces a runnable backend with SQLite, no docker required.
7. `verify_local_demo.sh` is green; new test files cover protocol, policy-runtime integration, streaming, behaviour-memory.
8. `README.md`, `INTEGRATION_GUIDE.md`, `ROAM_LOOP.md`, `INTERACTION_POLICY.md` updated; the legacy `MINI_SURFACE_REGISTRY.md` has already been removed in favour of `SURFACE_PROTOCOL.md`.

When (and only when) all 10 are true, we cut `v1.0` of `tilo-surface-protocol`.
