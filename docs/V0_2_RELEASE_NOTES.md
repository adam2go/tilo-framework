# Tilo Framework v0.2 Release Notes

v0.2 strengthens Tilo's core product loop:

```text
Conversation -> Task -> Run -> Memory Recall -> Skill Selection -> Tool Execution -> Artifact Generation -> Human Confirmation -> Memory Update
```

## Highlights

- Structured memory foundation with candidate lifecycle, recall logging, write events, salience, scope, and inspectable review UI.
- `artifact_spec.v1` with backend validation, renderer registry, actions, provenance, memory refs, and artifact detail pages.
- Safe self-improvement primitives: run metrics, feedback, skill candidates, approval/rejection, and promotion.
- Runtime hardening through explicit run/task state transitions, trace sanitization, and failed-run handling.
- Tool permission ledger with persisted tool invocations and confirmation gates for high-risk tools.
- Local eval scaffolding for memory recall, artifact schemas, and the end-to-end runtime loop.

## User-Facing Changes

- Console context panel now has Memory, Trace, Skills, and Files tabs.
- Inbox shows pending, approved, and rejected/edited confirmations with source task/run and risk context.
- Memory page separates candidates, confirmed memories, and rejected/archived memories.
- Skills page exposes pending skill candidates and promotion workflow.
- Artifact detail pages show title, status, version, linked task, linked run, trace link, memory refs, and provenance.

## Developer Notes

Run backend smoke tests:

```bash
pytest backend/tests/test_smoke.py
```

Run local evals:

```bash
python3 evals/runners/run_memory_recall_eval.py
python3 evals/runners/run_artifact_schema_eval.py
python3 evals/runners/run_runtime_loop_eval.py
```

The implementation remains intentionally local and mock-friendly. External destructive actions, automatic skill mutation, and unreviewed memory confirmation are still out of scope.
