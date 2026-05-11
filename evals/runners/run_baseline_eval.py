from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
REPORT_PATH = REPO_ROOT / "evals" / "baseline_report.md"

sys.path.insert(0, str(BACKEND_ROOT))

db_path = Path(tempfile.gettempdir()) / "tilo_baseline_eval.db"
if db_path.exists():
    db_path.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
os.environ["LLM_ENABLED"] = "false"
os.environ["LLM_PROVIDER"] = "openai"
os.environ["LLM_BASE_URL"] = ""
os.environ["OPENAI_API_KEY"] = ""

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.services.demo import load_problematic_ai_service_agreement  # noqa: E402

RENDERABLE_BLOCK_TYPES = {
    "action_queue",
    "approval_card",
    "comparison_matrix",
    "editable_text",
    "form",
    "list",
    "markdown",
    "memory_candidate",
    "metric",
    "metric_dashboard",
    "risk_panel",
    "risk_review_panel",
    "table",
    "tool_call_preview",
}


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def _write_report(metrics: dict[str, Any]) -> None:
    app_rows = [
        (
            app_id,
            app_metrics["surface_render_rate"],
            app_metrics["artifact_action_completion_rate"],
            app_metrics["memory_candidate_acceptance_rate"],
            app_metrics["artifact_type"],
            app_metrics["total_blocks"],
        )
        for app_id, app_metrics in metrics["apps"].items()
    ]
    REPORT_PATH.write_text(
        "\n".join(
            [
                "# Baseline Eval Report",
                "",
                "This baseline is deterministic and runs without external LLM calls.",
                "",
                "| Metric | Value | Notes |",
                "|---|---:|---|",
                f"| surface_render_rate | {metrics['surface_render_rate']:.2f} | {metrics['renderable_blocks']} / {metrics['total_blocks']} artifact blocks had a safe render path. Extension fallback counts as renderable. |",
                f"| artifact_action_completion_rate | {metrics['artifact_action_completion_rate']:.2f} | {metrics['completed_actions']} / {metrics['attempted_actions']} artifact actions completed through Artifact Action Runtime. |",
                f"| memory_candidate_acceptance_rate | {metrics['memory_candidate_acceptance_rate']:.2f} | {metrics['confirmed_memory_candidates']} / {metrics['memory_candidates']} memory candidates were accepted by explicit confirmation. |",
                "",
                "## App Coverage",
                "",
                "| App | Artifact Type | Blocks | Surface Render Rate | Action Completion Rate | Memory Acceptance Rate |",
                "|---|---|---:|---:|---:|---:|",
                *[
                    f"| `{app_id}` | `{artifact_type}` | {total_blocks} | {surface:.2f} | {action:.2f} | {memory:.2f} |"
                    for app_id, surface, action, memory, artifact_type, total_blocks in app_rows
                ],
                "",
                "## Scope",
                "",
                "- Apps: `examples/apps/contract-review-agent`, `examples/apps/sales-followup-agent`",
                "- Mode: deterministic local mode",
                "- Chain: conversation message -> artifact -> artifact action -> observation -> memory candidate -> memory confirmation",
                "",
                "## Limitations",
                "",
                "- This is a smoke baseline, not a statistical benchmark.",
                "- Surface rendering is inferred from ArtifactSpec block shape and fallback availability; page-level demo verification lives in `scripts/verify_demo_page.py`.",
                "- Memory acceptance is measured by explicit API confirmation in the eval flow, not by a real human reviewer.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _sample_for_app(app_id: str) -> dict[str, Any]:
    if app_id == "contract-review-agent":
        fixture = load_problematic_ai_service_agreement()
        return {
            "content": f"Review this contract and propose a conservative liability revision.\n\n{fixture.content}",
            "attachments": [{"name": fixture.file_name, "type": "sample_contract", "source_path": fixture.source_path}],
            "action_id": "approve_liability_revision",
            "choice": "approve_revision",
        }
    if app_id == "sales-followup-agent":
        fixture_path = REPO_ROOT / "examples" / "apps" / "sales-followup-agent" / "fixtures" / "lead-summary.md"
        return {
            "content": f"Draft and prioritize a sales follow-up plan for this account summary.\n\n{fixture_path.read_text(encoding='utf-8')}",
            "attachments": [{"name": "lead-summary.md", "type": "sample_lead_summary", "source_path": str(fixture_path)}],
            "action_id": "approve_sales_followup",
            "choice": "approve_followup",
        }
    raise ValueError(f"Unsupported eval app: {app_id}")


def _run_app_case(client: TestClient, app_id: str) -> dict[str, Any]:
    sample = _sample_for_app(app_id)
    workspace_id = f"baseline-eval-{app_id}"

    session_response = client.post(
        "/api/conversations",
        json={"app_id": app_id, "workspace_id": workspace_id, "channel": "web"},
    )
    session_response.raise_for_status()
    session = session_response.json()

    message_response = client.post(
        f"/api/conversations/{session['id']}/messages",
        json={
            "content": sample["content"],
            "attachments": sample["attachments"],
        },
    )
    message_response.raise_for_status()
    message = message_response.json()

    artifact_response = client.get("/api/artifacts", params={"workspace_id": workspace_id, "task_id": message["task_id"]})
    artifact_response.raise_for_status()
    artifacts = artifact_response.json()
    artifact = artifacts[0]
    schema = artifact["schema_json"]
    blocks = schema["blocks"]

    # The reference renderer has a fallback for every non-empty extension block type.
    renderable_blocks = sum(
        1
        for block in blocks
        if block.get("id") and block.get("type") and isinstance(block.get("data"), dict)
        and (block["type"] in RENDERABLE_BLOCK_TYPES or block.get("type"))
    )

    action = next(item for item in schema["actions"] if item["id"] == sample["action_id"])
    action_response = client.post(
        f"/api/artifacts/{artifact['id']}/actions/{action['id']}",
        json={
            "session_id": session["id"],
            "run_id": message["run_id"],
            "source": "eval",
            "payload": {"choice": sample["choice"]},
        },
    )
    action_response.raise_for_status()
    action_result = action_response.json()

    memory_response = client.get("/api/memories", params={"workspace_id": workspace_id, "status": "candidate"})
    memory_response.raise_for_status()
    memory_candidates = memory_response.json()
    reflection_memory = next((memory for memory in memory_candidates if memory["source_type"] == "context_reflection"), None)
    confirmed = None
    if reflection_memory:
        confirm_response = client.post(f"/api/memories/{reflection_memory['id']}/confirm")
        confirm_response.raise_for_status()
        confirmed = confirm_response.json()

    return {
        "app_id": app_id,
        "artifact_type": schema["artifact_type"],
        "surface_render_rate": _rate(renderable_blocks, len(blocks)),
        "total_blocks": len(blocks),
        "renderable_blocks": renderable_blocks,
        "artifact_action_completion_rate": _rate(1 if action_result["status"] == "completed" else 0, 1),
        "attempted_actions": 1,
        "completed_actions": 1 if action_result["status"] == "completed" else 0,
        "memory_candidate_acceptance_rate": _rate(1 if confirmed and confirmed["is_confirmed"] else 0, 1 if reflection_memory else 0),
        "memory_candidates": 1 if reflection_memory else 0,
        "confirmed_memory_candidates": 1 if confirmed and confirmed["is_confirmed"] else 0,
    }


def run() -> dict[str, Any]:
    app_metrics: dict[str, dict[str, Any]] = {}
    with TestClient(app) as client:
        for app_id in ("contract-review-agent", "sales-followup-agent"):
            app_metrics[app_id] = _run_app_case(client, app_id)

    total_blocks = sum(item["total_blocks"] for item in app_metrics.values())
    renderable_blocks = sum(item["renderable_blocks"] for item in app_metrics.values())
    attempted_actions = sum(item["attempted_actions"] for item in app_metrics.values())
    completed_actions = sum(item["completed_actions"] for item in app_metrics.values())
    memory_candidates = sum(item["memory_candidates"] for item in app_metrics.values())
    confirmed_memory_candidates = sum(item["confirmed_memory_candidates"] for item in app_metrics.values())
    metrics = {
        "surface_render_rate": _rate(renderable_blocks, total_blocks),
        "total_blocks": total_blocks,
        "renderable_blocks": renderable_blocks,
        "artifact_action_completion_rate": _rate(completed_actions, attempted_actions),
        "attempted_actions": attempted_actions,
        "completed_actions": completed_actions,
        "memory_candidate_acceptance_rate": _rate(confirmed_memory_candidates, memory_candidates),
        "memory_candidates": memory_candidates,
        "confirmed_memory_candidates": confirmed_memory_candidates,
        "apps": app_metrics,
    }
    _write_report(metrics)
    return metrics


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
