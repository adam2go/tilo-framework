CONTRACT_REVIEW_SYSTEM_PROMPT = """You are Tilo's contract review artifact generator.
Return JSON only. Do not include markdown, hidden reasoning, or commentary.
Focus on payment, liability, termination, confidentiality, and IP ownership risks.
Make suggestions conservative, actionable, and suitable for a generated ROAM artifact.
Match the output language to the user task. If the user asks for Simplified Chinese, every JSON string value must be Simplified Chinese. Keep JSON keys unchanged.
If the contract contains clauses 8.1 and 8.2 about liability caps and indemnity carve-outs, make that conflict the first risk. Generate enough findings for a full review artifact, but treat only the most decision-relevant issue as the primary mini-surface issue.
"""


def contract_review_user_prompt(task_message: str, memory_snippets: list[str], tool_outputs: list[dict]) -> str:
    return (
        "User task:\n"
        f"{task_message}\n\n"
        "Recalled memory snippets:\n"
        f"{memory_snippets[:5]}\n\n"
        "Tool output summaries:\n"
        f"{tool_outputs[:3]}\n\n"
        "Review behavior:\n"
        "- Read the full contract text in the user task.\n"
        "- Identify issues by clause number.\n"
        "- Put the liability cap / indemnity carve-out conflict first when clauses 8.1 and 8.2 are present.\n"
        "- Keep memory_candidate focused on user preference only; do not invent a memory until the user indicates a preference.\n\n"
        "Return this JSON object shape exactly:\n"
        "{\n"
        '  "risk_summary": {"high_count": 3, "medium_count": 2, "low_count": 1, "summary": "..."},\n'
        '  "risks": [{"id": "risk_1", "clause": "...", "risk_level": "high", "issue": "...", "suggested_revision": "...", "evidence": "..."}],\n'
        '  "revision_draft": {"heading": "Conservative revision draft", "content": "...", "highlights": ["..."]},\n'
        '  "memory_candidate": {"type": "preference", "content": "...", "confidence": 0.7}\n'
        "}\n"
    )
