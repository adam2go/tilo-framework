CONTRACT_REVIEW_SYSTEM_PROMPT = """You are Tilo's contract review artifact generator.
Return JSON only. Do not include markdown, hidden reasoning, or commentary.
Focus on payment, liability, termination, confidentiality, and IP ownership risks.
Make suggestions conservative, actionable, and suitable for a generated ROAM artifact.
"""


def contract_review_user_prompt(task_message: str, memory_snippets: list[str], tool_outputs: list[dict]) -> str:
    return (
        "User task:\n"
        f"{task_message}\n\n"
        "Recalled memory snippets:\n"
        f"{memory_snippets[:5]}\n\n"
        "Tool output summaries:\n"
        f"{tool_outputs[:3]}\n\n"
        "Return this JSON object shape exactly:\n"
        "{\n"
        '  "risk_summary": {"high_count": 3, "medium_count": 2, "low_count": 1, "summary": "..."},\n'
        '  "risks": [{"id": "risk_1", "clause": "...", "risk_level": "high", "issue": "...", "suggested_revision": "...", "evidence": "..."}],\n'
        '  "revision_draft": {"heading": "Conservative revision draft", "content": "...", "highlights": ["..."]},\n'
        '  "memory_candidate": {"type": "preference", "content": "...", "confidence": 0.7}\n'
        "}\n"
    )
