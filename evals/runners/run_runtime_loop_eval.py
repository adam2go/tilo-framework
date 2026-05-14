import json
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(tempfile.gettempdir()) / "tilo_runtime_eval.db"
if DB_PATH.exists():
    DB_PATH.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH}"
BACKEND_PATH = ROOT / "backend"
sys.path.insert(0, str(BACKEND_PATH if BACKEND_PATH.exists() else ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from tilo.main import app  # noqa: E402


DATASET = ROOT / "evals" / "datasets" / "contract_review_cases.jsonl"
REPORT = ROOT / "evals" / "reports" / "runtime_loop_report.json"


def main() -> None:
    cases = [json.loads(line) for line in DATASET.read_text().splitlines() if line.strip()]
    results = []
    with TestClient(app) as client:
        bootstrap = client.get("/api/bootstrap").json()
        workspace = bootstrap["workspace"]
        project = bootstrap["projects"][0]
        agent = bootstrap["agents"][0]

        for case in cases:
            message = client.post(
                "/api/messages",
                json={
                    "workspace_id": workspace["id"],
                    "project_id": project["id"],
                    "agent_id": agent["id"],
                    "content": case["message"],
                    "attachments": [],
                },
            ).json()
            artifacts = client.get("/api/artifacts", params={"workspace_id": workspace["id"], "task_id": message["task_id"]}).json()
            trace = client.get(f"/api/runs/{message['run_id']}/trace").json()
            confirmations = client.get("/api/confirmations", params={"workspace_id": workspace["id"], "status": "pending"}).json()
            memories = client.get("/api/memories", params={"workspace_id": workspace["id"], "status": "candidate"}).json()
            tool_invocations = client.get("/api/tools/invocations", params={"workspace_id": workspace["id"], "run_id": message["run_id"]}).json()
            ok = (
                message["status"] == "completed"
                and bool(artifacts)
                and artifacts[0]["schema_json"]["artifact_type"] == case["expect_artifact_type"]
                and bool(trace)
                and bool(tool_invocations)
                and (not case["expect_confirmation"] or bool(confirmations))
                and (not case["expect_memory_candidate"] or bool(memories))
            )
            results.append({"id": case["id"], "success": ok, "run_id": message["run_id"], "artifact_count": len(artifacts), "trace_count": len(trace)})

    report = {
        "case_count": len(cases),
        "end_to_end_loop_success_rate": sum(1 for result in results if result["success"]) / max(len(results), 1),
        "results": results,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
