import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "datasets" / "memory_recall_cases.jsonl"
REPORT = ROOT / "reports" / "memory_recall_report.json"


def tokenize(text: str) -> set[str]:
    return {word.strip(".,!?;:()[]{}\"'").lower() for word in text.split() if len(word.strip(".,!?;:()[]{}\"'")) > 3}


def score(query: str, memory: dict) -> float:
    query_words = tokenize(query)
    content_words = tokenize(memory["content"])
    if not query_words:
        return 0.0
    return len(query_words & content_words) / len(query_words)


def main() -> None:
    cases = [json.loads(line) for line in DATASET.read_text().splitlines() if line.strip()]
    hits = 0
    precision_sum = 0.0
    false_positive_sum = 0.0
    results = []

    for case in cases:
        ranked = sorted(case["memories"], key=lambda memory: score(case["query"], memory), reverse=True)
        top_ids = [memory["id"] for memory in ranked[:5]]
        expected = set(case["expected_memory_ids"])
        matched = expected & set(top_ids)
        false_positives = [memory_id for memory_id in top_ids if memory_id not in expected]
        hits += 1 if matched else 0
        precision_sum += len(matched) / max(len(top_ids), 1)
        false_positive_sum += len(false_positives) / max(len(top_ids), 1)
        results.append({"id": case["id"], "top_ids": top_ids, "expected_memory_ids": sorted(expected), "matched": sorted(matched)})

    report = {
        "case_count": len(cases),
        "recall_hit_rate@5": hits / max(len(cases), 1),
        "precision@5": precision_sum / max(len(cases), 1),
        "false_positive_rate": false_positive_sum / max(len(cases), 1),
        "results": results,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
