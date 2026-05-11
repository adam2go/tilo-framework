# Baseline Eval Report

This baseline is deterministic and runs without external LLM calls.

| Metric | Value | Notes |
|---|---:|---|
| surface_render_rate | 1.00 | 8 / 8 artifact blocks had a safe render path. Extension fallback counts as renderable. |
| artifact_action_completion_rate | 1.00 | 2 / 2 artifact actions completed through Artifact Action Runtime. |
| memory_candidate_acceptance_rate | 1.00 | 2 / 2 memory candidates were accepted by explicit confirmation. |

## App Coverage

| App | Artifact Type | Blocks | Surface Render Rate | Action Completion Rate | Memory Acceptance Rate |
|---|---|---:|---:|---:|---:|
| `contract-review-agent` | `contract_review` | 5 | 1.00 | 1.00 | 1.00 |
| `sales-followup-agent` | `dashboard` | 3 | 1.00 | 1.00 | 1.00 |

## Scope

- Apps: `examples/apps/contract-review-agent`, `examples/apps/sales-followup-agent`
- Mode: deterministic local mode
- Chain: conversation message -> artifact -> artifact action -> observation -> memory candidate -> memory confirmation

## Limitations

- This is a smoke baseline, not a statistical benchmark.
- Surface rendering is inferred from ArtifactSpec block shape and fallback availability; page-level demo verification lives in `scripts/verify_demo_page.py`.
- Memory acceptance is measured by explicit API confirmation in the eval flow, not by a real human reviewer.
