import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND_PATH = ROOT / "backend"
sys.path.insert(0, str(BACKEND_PATH if BACKEND_PATH.exists() else ROOT))

from app.schemas.artifact import ArtifactSpecV1, SUPPORTED_BLOCK_TYPES  # noqa: E402


DATASET = ROOT / "evals" / "datasets" / "artifact_schema_cases.jsonl"
REPORT = ROOT / "evals" / "reports" / "artifact_schema_report.json"
FRONTEND_RENDERERS = {
    "markdown",
    "rich_text",
    "table",
    "metric",
    "card",
    "list",
    "timeline",
    "kanban",
    "risk_item",
    "confirmation_action",
    "comparison_matrix",
}


def main() -> None:
    cases = [json.loads(line) for line in DATASET.read_text().splitlines() if line.strip()]
    valid_count = 0
    unsupported_blocks = 0
    block_count = 0
    renderable_count = 0
    results = []

    for case in cases:
        is_valid = True
        error = None
        try:
            spec = ArtifactSpecV1.model_validate(case["schema"])
            valid_count += 1
            blocks = spec.blocks
        except Exception as exc:
            is_valid = False
            error = str(exc)
            blocks = []

        for block in case["schema"].get("blocks", []):
            block_count += 1
            if block.get("type") not in SUPPORTED_BLOCK_TYPES:
                unsupported_blocks += 1
            if block.get("type") in FRONTEND_RENDERERS:
                renderable_count += 1

        results.append({"id": case["id"], "valid": is_valid, "expected_valid": case["expected_valid"], "error": error})

    report = {
        "case_count": len(cases),
        "artifact_schema_valid_rate": valid_count / max(len(cases), 1),
        "unsupported_block_rate": unsupported_blocks / max(block_count, 1),
        "render_success_rate": renderable_count / max(block_count, 1),
        "results": results,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
