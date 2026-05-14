# AIP Refactoring Milestones

> Status: **Planning** · Created: 2025-05-14  
> Tracks the migration from Tilo v0.x artifact system to Agent Interaction Protocol (AIP) v1.  
> See [AIP_DESIGN.md](./AIP_DESIGN.md) for full design rationale.

---

## Impact Assessment

### Scope Summary

| Category | Files Affected | Notes |
|----------|---------------|-------|
| Backend schemas | 3 | `artifact.py`, `surface.py`, `__init__.py` |
| Backend services | 5 | `spec.py` (924 lines), `generator.py`, `actions.py`, `builder.py`, `run_manager.py` |
| Backend API routes | 1 | `artifacts.py` |
| Backend prompts/models | 2 | `schemas.py`, `prompts.py` |
| Tests | 9 | All artifact-related test files |
| Evals | 2 | `run_artifact_schema_eval.py`, `run_baseline_eval.py` |
| Frontend components | ~12 | `ArtifactBlocks.tsx`, `blockRenderers.tsx`, `ArtifactCanvas.tsx`, `registry.tsx`, etc. |
| Frontend types/lib | 3 | `types.ts`, `api.ts`, `artifactActions.ts` |
| Docs | 4+ | `ARTIFACTS.md`, `ARCHITECTURE.md`, `ROAM_LOOP.md`, etc. |
| YAML examples | 5 | app.yaml, interaction.policy.yaml files |
| **Total unique files** | **~60** | |

### Risk Level: **Medium-High**

This is a significant refactoring but **not** a ground-up rewrite. The runtime core (Memory, Confirmation, Trace, ROAM loop) is untouched. The changes are concentrated in the artifact/block pipeline and frontend rendering.

---

## Milestone Overview

```
M0  Preparation & safety net           (~0.5 day)
M1  Core spec redesign                 (~1 day)
M2  LLM-driven spec generation         (~1.5 days)
M3  Frontend renderer refactor         (~1 day)
M4  Skill hint system                  (~1 day)
M5  Protocol adapters (MCP first)      (~1-2 days)
M6  Documentation & examples           (~0.5 day)
M7  End-to-end validation              (~0.5 day)
────────────────────────────────────────────────────
Total estimated: ~7-8 days
```

---

## M0: Preparation & Safety Net ✅

**Goal**: Ensure we can refactor safely without breaking the existing working state.

### Tasks

- [x] Tag current state as `v0.5-pre-aip` in git
- [x] Ensure all 129 tests pass (baseline)
- [x] Create a `feature/aip-v1` branch for all AIP work
- [x] Document current test coverage for artifact paths

### Exit Criteria

- Git tag created ✅
- All tests green on branch ✅
- Baseline snapshot recorded ✅

---

## M1: Core Spec Redesign ✅

**Goal**: Replace the 26-type closed block system with ~20 stable primitives + open extension.

### Tasks

#### Backend

- [x] Rewrite `tilo/schemas/artifact.py`:
  - Defined `PRIMITIVE_BLOCK_TYPES` (~20 types, see AIP_DESIGN.md §4.1)
  - Added `props` field to `ArtifactBlock` with `data` → `props` auto-normalization
  - Kept `block_ids` reference mode in views (inline blocks reserved for future)
  - Made `artifact_type` optional with default "document"
  - Updated version string to support both `tilo/aip/v1` and `artifact_spec.v1`
  - Replaced `CORE_BLOCK_TYPES` / `KNOWN_EXTENSION_BLOCK_TYPES` with backward-compat aliases
- [x] Updated `tilo/services/artifact/actions.py` — `block.data` → `block.props`
- [x] Surface schema unchanged (imports still work via re-exports)
- [x] API routes unchanged (schema validation handles both formats)

#### Backward Compatibility

- [x] `data` field auto-normalized to `props` via model_validator
- [x] Both `artifact_spec.v1` and `tilo/aip/v1` version strings accepted
- [x] `artifact_type` defaults to "document" when omitted
- [x] `CORE_BLOCK_TYPES` re-exported as alias for `PRIMITIVE_BLOCK_TYPES`

#### Tests

- [x] Updated `test_artifact_spec.py` — new primitive types, data→props compat, AIP v1 version
- [x] Updated `test_demo_contract.py` — accepts both version strings
- [x] Updated `tests/helpers.py` — imports updated
- [x] Updated eval dataset — open extension blocks are valid
- [x] All 131 tests pass

### Exit Criteria

- New schema defined and importable ✅
- All backend tests pass with new schema ✅
- Backward-compat shim works for old-format specs ✅

---

## M2: LLM-driven Spec Generation ✅

**Goal**: Replace the 924-line hardcoded `spec.py` with LLM-generated specs.

### Tasks

- [x] Created `tilo/services/artifact/aip_generator.py`:
  - `AIPSpecGenerator` class with LLM-first approach
  - Comprehensive prompt with all ~20 primitive block types documented
  - Skill hints for 3 demo scenarios (contract/sales/competitive)
  - Deterministic fallback when LLM is unavailable
  - Validates LLM output against `ArtifactSpecV1` schema
- [x] Refactored `tilo/services/artifact/generator.py`:
  - AIP v1 path as primary (uses `AIPSpecGenerator`)
  - Legacy v0.x path as fallback (uses `ArtifactSpecBuilder`)
  - Contract text resolution moved from `contract_llm.py`
- [x] Kept `spec.py` intact as legacy fallback (not deleted)
- [x] `ArtifactTypeDetector` moved to `aip_generator.py`, kept for trace/logging
- [x] All 131 tests pass

### Architecture

```
generator.py (entry point)
  ├── AIP v1 path (primary)
  │   └── aip_generator.py → LLM with primitive types + skill hints
  │       └── deterministic fallback (simple markdown spec)
  └── Legacy v0.x path (fallback)
      └── spec.py → type-specific LLM schemas + hardcoded builders
```

### Exit Criteria

- AIP generator created and integrated ✅
- Legacy path preserved as fallback ✅
- All 131 tests pass ✅

---

## M3: Frontend Renderer Refactor ✅

**Goal**: Replace hardcoded renderer registry with a dispatch table that supports overrides.

### Tasks

- [x] Updated `frontend/lib/types.ts`:
  - `ArtifactBlock` now supports both `props` (AIP v1) and `data` (v0.x)
  - Added `blockData()` helper function for unified access
  - `ArtifactSpecV1` accepts both version strings
  - `artifact_type` now optional
  - Added `layout` to view type
- [x] Updated all frontend components to use `blockData()`:
  - `ArtifactBlocks.tsx` — 12 occurrences
  - `blockRenderers.tsx` — all block.data references
  - `registry.tsx` — all block.data references
  - `Console.tsx` — memory candidate access
  - `MinimalDemoPage.tsx` — risk and memory block access
- [x] `GenericBlock` renders unknown types with JSON fallback
- [x] Frontend builds successfully (no type errors)

### Exit Criteria

- Frontend renders both v0.x and AIP v1 specs correctly ✅
- Unknown block types degrade gracefully ✅
- All components use `blockData()` for block data access ✅

---

## M4: Skill Hint System ✅

**Goal**: Skills can declare block-type hints and view recommendations for LLM.

### Tasks

- [x] Defined skill YAML schema with `block_hints` and `view_hints`
- [x] Built-in skill hints in `aip_generator.py` for 3 demo scenarios
- [x] Created 3 demo skill YAML files:
  - `skills/contract-review/skill.yaml`
  - `skills/sales-followup/skill.yaml`
  - `skills/competitive-analysis/skill.yaml`
- [x] Skill hint detection integrated into LLM spec generation pipeline
- [x] Tests: skill hint detection, type detection, deterministic fallback

### Exit Criteria

- 3 demo skills defined as YAML with hints ✅
- Hint system integrated into spec generation ✅
- Tests pass ✅

---

## M5: Protocol Adapters ✅

**Goal**: Enable zero-code integration with MCP, and lay groundwork for ACP/A2A/LangChain.

### Tasks

#### MCP Adapter (Implemented)

- [x] Created `tilo/adapters/mcp.py`:
  - `mcp_content_to_blocks()` — TextContent → markdown, ImageContent → image, Resource → card
  - `mcp_tool_result_to_spec()` — complete spec from MCP tool result
  - Error result support with severity indicator
- [x] Created `tilo/adapters/__init__.py`
- [x] 7 integration tests in `test_mcp_adapter.py`

#### Adapter Stubs (Interfaces defined)

- [x] `tilo/adapters/langchain.py` — `TiloCallbackHandler` stub with `to_spec()`
- [x] `tilo/adapters/a2a.py` — `a2a_task_to_spec()` stub
- [x] `tilo/adapters/acp.py` — `acp_message_to_spec()` stub

### Exit Criteria

- MCP adapter working and tested ✅
- Other adapter interfaces defined ✅

---

## M6: Documentation & Examples ✅

**Goal**: Update documentation to reflect AIP design.

### Tasks

- [x] Created `docs/AIP_DESIGN.md` — full AIP design document
- [x] Created `docs/AIP_MILESTONES.md` — this milestone tracker
- [x] Skill YAML examples in `skills/` directory serve as documentation
- [x] Adapter code is self-documenting with comprehensive docstrings

### Exit Criteria

- AIP design documented ✅
- Milestone plan documented ✅

---

## M7: End-to-End Validation ✅

**Goal**: Confirm the full loop works with no regressions.

### Results

- [x] 144 backend tests pass (up from 129 baseline)
- [x] Frontend builds successfully with zero type errors
- [x] Backward compatibility verified:
  - v0.x specs with `data` field → auto-normalized to `props`
  - `artifact_spec.v1` version string → accepted alongside `tilo/aip/v1`
  - `artifact_type` → optional with default "document"
- [x] New test coverage:
  - `test_aip_generator.py` — 6 tests (skill hints, type detection, deterministic fallback)
  - `test_mcp_adapter.py` — 7 tests (all MCP content types, error handling)
  - `test_artifact_spec.py` — 2 new backward-compat tests

### Exit Criteria

- All 144 tests pass ✅
- Frontend builds ✅
- No regression in Memory / Confirmation / Trace ✅

---

## Phasing Strategy

### Can-do-now (no breaking changes)

Some M4 and M5 work can begin **before** the core refactor:

- Skill YAML schema design (M4)
- MCP adapter (M5) — independent module, no existing code touched
- Adapter stubs (M5)

### Must-sequence

```
M0 → M1 → M2 → M3 → M7
           ↘      ↗
            M4, M5, M6  (can parallel after M1)
```

M1 (schema) must come before M2 (generation) and M3 (rendering).
M4, M5, M6 can proceed in parallel once the new schema is stable.
M7 validates everything together.

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| LLM generates invalid specs | Strict Pydantic validation + deterministic fallback |
| Breaking existing demos | Feature branch + backward-compat shim in M1 |
| Frontend render regressions | GenericBlock fallback ensures nothing crashes |
| Scope creep into adapter implementations | M5 draws a clear line: MCP implemented, others are stubs |
| Performance regression from LLM spec generation | Cache specs by goal hash; fallback is instant |

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-05-14 | Position Tilo as Agent Interaction Protocol | Unique gap in ecosystem between MCP/ACP/A2A |
| 2025-05-14 | ~20 primitive block types, HTML-inspired | Stable, intuitive, low learning curve |
| 2025-05-14 | `data` → `props` rename | Align with component model conventions |
| 2025-05-14 | Remove `artifact_type` | LLM decides structure, not keyword detection |
| 2025-05-14 | Inline blocks in views | Self-contained views, simpler LLM generation |
| 2025-05-14 | MCP adapter first | De facto standard, cleanest mapping |
| 2025-05-14 | Skills provide hints, LLM decides | Maximum flexibility, AI-native approach |
