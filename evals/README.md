# Tilo v0.2 Evals

These local evals exercise framework behavior without external paid APIs.

Run from the repository root:

```bash
python3 evals/runners/run_memory_recall_eval.py
python3 evals/runners/run_artifact_schema_eval.py
python3 evals/runners/run_runtime_loop_eval.py
```

The runners are intentionally lightweight. They validate the v0.2 contracts:

- memory recall prefers relevant confirmed memories
- artifacts conform to `artifact_spec.v1`
- the runtime loop creates Task, Run, TraceStep, Artifact, Confirmation, Memory, and ToolInvocation records

Reports are written to `evals/reports/`.
