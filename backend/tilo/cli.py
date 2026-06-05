"""Tilo CLI — lightweight entry points for the framework.

Usage after `pip install tilo`:

    tilo serve                   Start the API server (welcome page + playground)
    tilo serve --port 9000
    tilo serve --reload          Auto-reload on code changes (dev mode)
    tilo init myproject          Scaffold a complete, runnable Tilo project
    tilo demo                    Open a sample surface in your browser instantly
    tilo version                 Print version and exit
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="tilo",
        description="Tilo — turn any LLM into an interactive UI.",
        epilog=(
            "Examples:\n"
            "  tilo demo                 Open a sample surface in your browser\n"
            "  tilo init myapp           Scaffold a project (hello.py uses your LLM)\n"
            "  tilo serve                Start the API + live /playground\n"
            "\n"
            "In Python:\n"
            "  import tilo\n"
            "  spec = tilo.generate('Review this contract', model='gpt-4o')\n"
            "  tilo.view(spec)           # opens in your browser, no React needed\n"
            "\n"
            "Set OPENAI_API_KEY (or ANTHROPIC_API_KEY) for live generation.\n"
            "Docs: https://github.com/adam2go/tilo-framework"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    serve_p = sub.add_parser("serve", help="Start the Tilo API server")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=8000)
    serve_p.add_argument("--reload", action="store_true", default=False)

    init_p = sub.add_parser("init", help="Scaffold a complete Tilo project")
    init_p.add_argument("name", nargs="?", default="my-tilo-app")

    gen_p = sub.add_parser("generate", help="Generate a surface from a goal and open it")
    gen_p.add_argument("goal", help="What the surface should address, e.g. 'Review this contract'")
    gen_p.add_argument("--model", default=None, help="Model name (gpt-4o, claude-opus-4-8, …)")
    gen_p.add_argument("--base-url", default=None, help="OpenAI-compatible endpoint (DeepSeek, Groq, OpenRouter, local …)")
    gen_p.add_argument("--skill", default="auto", help="Skill hint or 'auto' (default)")
    gen_p.add_argument("--document", default=None, help="Path to a document to ground the surface")
    gen_p.add_argument("--temperature", type=float, default=0.3, help="0.0 deterministic … 1.0 creative")
    gen_p.add_argument("--json", action="store_true", help="Print the spec as JSON instead of opening a browser")
    gen_p.add_argument("--html", default=None, metavar="PATH", help="Save a standalone HTML file instead of opening a browser")
    gen_p.add_argument("--save", default=None, metavar="PATH", help="Also save the spec as JSON to PATH")

    sub.add_parser("demo", help="Open a sample Tilo surface in your browser")
    sub.add_parser("version", help="Print version")

    args = parser.parse_args(argv)

    if args.command == "serve":
        _serve(args)
    elif args.command == "init":
        _init(args)
    elif args.command == "generate":
        _generate(args)
    elif args.command == "demo":
        _demo()
    elif args.command == "version":
        _version()
    else:
        parser.print_help()


def _serve(args: argparse.Namespace) -> None:
    try:
        import uvicorn
    except ImportError:
        print("uvicorn is required. Install with: pip install 'tilo[standard]'")
        sys.exit(1)

    print(f"▶  Tilo        →  http://{args.host}:{args.port}")
    print(f"   Playground  →  http://{args.host}:{args.port}/playground")
    print(f"   API docs    →  http://{args.host}:{args.port}/docs")
    print()

    uvicorn.run(
        "tilo.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def _demo() -> None:
    """Open a sample surface in the browser — instant 'what is Tilo'."""
    from tilo.viewer import view

    print("Opening a sample Tilo surface in your browser... (Ctrl-C to exit)")
    view(_DEMO_SPEC)


def _generate(args: argparse.Namespace) -> None:
    """`tilo generate "goal" [--model …]` — generate a surface from the shell."""
    import json as _json

    from tilo.generate import TiloGenerationError, generate

    document = None
    if args.document:
        from pathlib import Path
        doc_path = Path(args.document)
        if not doc_path.exists():
            print(f"Document not found: {args.document}")
            sys.exit(1)
        document = doc_path.read_text(encoding="utf-8")

    try:
        spec = generate(
            args.goal,
            model=args.model,
            base_url=args.base_url,
            skill=args.skill,
            document=document,
            temperature=args.temperature,
        )
    except (TiloGenerationError, ImportError, ValueError) as exc:
        print(f"✗ {exc}")
        sys.exit(1)

    print(f"✓ {spec.title}  ({len(spec.blocks)} blocks, {len(spec.views)} views)")

    if args.save:
        from tilo.viewer import save_spec
        path = save_spec(spec, args.save)
        print(f"  spec saved → {path}")

    if args.json:
        print(_json.dumps(spec.model_dump(), indent=2, ensure_ascii=False))
        return

    if args.html:
        from tilo.viewer import save_html
        path = save_html(spec, args.html)
        print(f"  html saved → {path}")
        return

    from tilo.viewer import view
    print("  opening in your browser... (Ctrl-C to exit)")
    view(spec)


def _init(args: argparse.Namespace) -> None:
    """Scaffold a complete, immediately-runnable Tilo project."""
    name = args.name
    root = Path(name)
    if root.exists():
        print(f"Directory '{name}' already exists.")
        sys.exit(1)

    root.mkdir(parents=True)

    (root / ".env").write_text(
        "# Tilo environment\n"
        "# SQLite is used by default — no Docker or Postgres needed.\n"
        "DATABASE_URL=sqlite:///tilo.db\n"
        "\n"
        "# Your LLM key (used by hello.py). Pick one provider.\n"
        "OPENAI_API_KEY=\n"
        "# ANTHROPIC_API_KEY=\n"
    )

    (root / "requirements.txt").write_text(
        "tilo\n"
        "openai  # or: anthropic\n"
    )

    (root / "hello.py").write_text(_HELLO_PY)
    (root / "server_demo.py").write_text(_SERVER_DEMO_PY)
    (root / "README.md").write_text(_readme(name))

    print(f"✓ Created '{name}/'\n")
    print("  Files:")
    print(f"    {name}/.env             — set your OPENAI_API_KEY here")
    print(f"    {name}/hello.py         — one-line LLM → rendered surface")
    print(f"    {name}/server_demo.py   — full ROAM-loop demo (optional)")
    print(f"    {name}/README.md        — project docs\n")
    print("  Get started:")
    print(f"    cd {name}")
    print("    pip install -r requirements.txt")
    print("    # add your key to .env, then:")
    print("    python hello.py        # opens a rendered surface in your browser")


def _version() -> None:
    try:
        from importlib.metadata import version
        v = version("tilo")
    except Exception:
        v = "0.1.0 (dev)"
    print(f"tilo {v}")


# --------------------------------------------------------------------------- #
# Scaffolded file contents                                                     #
# --------------------------------------------------------------------------- #

_HELLO_PY = '''"""Hello Tilo — from any LLM to a rendered interactive surface in one line.

Set OPENAI_API_KEY in .env (or your shell), then:
    python hello.py
"""

import os
import tilo

# Load .env if python-dotenv is available (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def main() -> None:
    if not (os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")):
        print("No API key found. Add OPENAI_API_KEY to .env, or run: tilo demo")
        return

    model = "gpt-4o-mini" if os.environ.get("OPENAI_API_KEY") else "claude-haiku-4-5-20251001"

    # The LLM generates a full interactive surface — chart, diff, checklist,
    # confirmation, memory card — organised into tabbed views.
    spec = tilo.generate(
        "Review this SaaS contract for payment, liability, and IP risks. "
        "It has an unlimited liability clause and net-60 payment terms.",
        model=model,
        skill="contract_review",
    )

    print(f"Generated: {spec.title}")
    print(f"Blocks:    {[b.type for b in spec.blocks]}")
    print("Opening in your browser...")

    tilo.view(spec)  # no React, no build step — just renders


if __name__ == "__main__":
    main()
'''

_SERVER_DEMO_PY = '''"""Full ROAM-loop demo — uses the Tilo backend (sessions, runs, memory).

Run the server first:
    tilo serve
Then in another terminal:
    python server_demo.py
"""

import json
import urllib.request

BASE = "http://127.0.0.1:8000"


def post(path: str, body: dict) -> dict:
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main() -> None:
    session = post("/api/conversations", {
        "app_id": "contract-review-agent",
        "workspace_id": "demo-workspace",
        "channel": "web",
    })
    print(f"Session: {session['id']}")

    result = post(f"/api/conversations/{session['id']}/messages", {
        "content": "Review this SaaS contract and flag any risks.",
        "attachments": [],
    })
    run = result.get("run", {})
    print(f"Run status: {run.get('status', 'unknown')}")
    print("Open http://127.0.0.1:8000/playground to render any spec.")


if __name__ == "__main__":
    main()
'''


def _readme(name: str) -> str:
    return f"""# {name}

A [Tilo](https://github.com/adam2go/tilo-framework)-powered AI project.

## Quick start

```bash
pip install -r requirements.txt
# add your OPENAI_API_KEY to .env, then:
python hello.py
```

`hello.py` asks an LLM to generate a full interactive surface and opens it
in your browser — charts, diffs, checklists, confirmations, memory cards.
No React, no build step.

## Render in your own React app

```bash
npm install @adam2go/tilo-react recharts lucide-react
```

```tsx
import {{ renderArtifactBlock }} from "@adam2go/tilo-react";

// spec comes from your backend (the same dict hello.py generates)
{{spec.blocks.map(b => <div key={{b.id}}>{{renderArtifactBlock(b)}}</div>)}}
```

## Full ROAM loop (sessions, runs, confirmed memory)

```bash
tilo serve            # starts the backend + playground at :8000
python server_demo.py # runs a full conversation → run → artifact
```

## Links

- [Tilo Framework](https://github.com/adam2go/tilo-framework)
- [Docs](https://github.com/adam2go/tilo-framework/tree/main/docs)
- [PyPI: tilo](https://pypi.org/project/tilo/)
- [npm: @adam2go/tilo-react](https://www.npmjs.com/package/@adam2go/tilo-react)
"""


_DEMO_SPEC = {
    "version": "tilo/aip/v1",
    "title": "Contract Risk Review",
    "status": "ready",
    "blocks": [
        {"id": "h", "type": "heading", "props": {"text": "2 High-Risk Clauses Found", "severity": "high"}},
        {"id": "m1", "type": "metric", "props": {"label": "Risk Score", "value": "7.2", "delta": "+1.1"}},
        {"id": "m2", "type": "metric", "props": {"label": "Clauses", "value": "24"}},
        {"id": "chart", "type": "chart", "title": "Risk by Category",
         "props": {"chart_type": "radar", "axes": [
             {"label": "Liability", "score": 9}, {"label": "Payment", "score": 6},
             {"label": "IP", "score": 8}, {"label": "Termination", "score": 3},
             {"label": "Confidentiality", "score": 5}]}},
        {"id": "diff", "type": "diff", "props": {
            "before": "Company shall have unlimited liability for all damages.",
            "after": "Company liability shall not exceed fees paid in the prior 12 months."}},
        {"id": "cl", "type": "checklist", "props": {"items": [
            {"text": "Review liability cap", "checked": True},
            {"text": "Confirm net-60 payment terms"},
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
        "Explain the IP ownership risk",
        "Save these preferences as a template",
    ],
}


if __name__ == "__main__":
    main()
