"""Tilo quickstart — from any LLM to a rendered interactive surface in one line.

This is the fastest way to see what Tilo does.

Requirements:
    pip install tilo openai      # or: anthropic

Usage:
    export OPENAI_API_KEY=sk-...
    python examples/integrations/quickstart.py

    # No API key? It still runs — shows a deterministic sample surface.
"""

from __future__ import annotations

import os


def main() -> None:
    has_openai = bool(os.environ.get("OPENAI_API_KEY"))
    has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))

    import tilo

    if has_openai:
        print("Generating a contract review surface with gpt-4o-mini...\n")
        spec = tilo.generate(
            "Review this SaaS contract for payment, liability, and IP risks. "
            "The contract has an unlimited liability clause and net-60 payment terms.",
            model="gpt-4o-mini",
            skill="contract_review",
        )
    elif has_anthropic:
        print("Generating a contract review surface with Claude...\n")
        spec = tilo.generate(
            "Review this SaaS contract for payment, liability, and IP risks.",
            model="claude-haiku-4-5-20251001",
            skill="contract_review",
        )
    else:
        print("No API key found — showing a deterministic sample surface.\n")
        spec = _sample_spec()

    # Show what the LLM produced
    print(f"Title:  {spec['title'] if isinstance(spec, dict) else spec.title}")
    blocks = spec["blocks"] if isinstance(spec, dict) else [b.model_dump() for b in spec.blocks]
    print(f"Blocks: {[b['type'] for b in blocks]}\n")

    # THE KILLER LINE: render it in the browser, no React needed
    print("Opening in your browser... (Ctrl-C to exit)\n")
    tilo.view(spec)


def _sample_spec() -> dict:
    return {
        "version": "tilo/aip/v1",
        "title": "Contract Risk Review",
        "status": "ready",
        "blocks": [
            {"id": "h", "type": "heading", "props": {"text": "2 High-Risk Clauses Found", "severity": "high"}},
            {"id": "m1", "type": "metric", "props": {"label": "Risk Score", "value": "7.2", "delta": "+1.1"}},
            {"id": "m2", "type": "metric", "props": {"label": "Clauses Reviewed", "value": "24"}},
            {"id": "chart", "type": "chart", "title": "Risk by Category",
             "props": {"chart_type": "radar", "axes": [
                 {"label": "Liability", "score": 9}, {"label": "Payment", "score": 6},
                 {"label": "IP", "score": 8}, {"label": "Termination", "score": 3},
                 {"label": "Confidentiality", "score": 4}]}},
            {"id": "diff", "type": "diff", "props": {
                "before": "Company shall have unlimited liability for all damages.",
                "after": "Company liability shall not exceed fees paid in the prior 12 months."}},
            {"id": "cl", "type": "checklist", "props": {"items": [
                {"text": "Review liability cap", "checked": True},
                {"text": "Confirm net-60 payment terms are acceptable"},
                {"text": "Verify IP ownership clause"}]}},
            {"id": "conf", "type": "confirmation", "props": {
                "description": "Approve revised contract with capped liability?", "risk_level": "high"}},
            {"id": "mem", "type": "memory_card", "props": {
                "content": "User prefers liability capped at 12-month fees", "confidence": 0.85}},
        ],
        "views": [
            {"id": "v1", "label": "Risks", "block_ids": ["h", "m1", "m2", "chart"]},
            {"id": "v2", "label": "Revision", "block_ids": ["diff", "cl"]},
            {"id": "v3", "label": "Decision", "block_ids": ["conf", "mem"]},
        ],
        "follow_ups": [
            "Compare the liability cap to industry standard",
            "Draft a counter-proposal email",
            "Explain the IP ownership risk in detail",
            "Save these preferences as a review template",
        ],
    }


if __name__ == "__main__":
    main()
