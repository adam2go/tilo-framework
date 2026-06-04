"""Tilo CLI — lightweight entry points for the framework.

Usage after `pip install tilo`:

    tilo serve                   Start the API server (uvicorn + SQLite, no Docker)
    tilo serve --port 9000
    tilo serve --reload          Auto-reload on code changes (dev mode)
    tilo init myproject          Scaffold a complete, runnable Tilo project
    tilo version                 Print version and exit
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="tilo",
        description="Tilo — AI-native product runtime framework",
    )
    sub = parser.add_subparsers(dest="command")

    # tilo serve
    serve_p = sub.add_parser("serve", help="Start the Tilo API server")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=8000)
    serve_p.add_argument("--reload", action="store_true", default=False)

    # tilo init
    init_p = sub.add_parser("init", help="Scaffold a complete Tilo project")
    init_p.add_argument("name", nargs="?", default="my-tilo-app")

    # tilo version
    sub.add_parser("version", help="Print version")

    args = parser.parse_args(argv)

    if args.command == "serve":
        _serve(args)
    elif args.command == "init":
        _init(args)
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

    print(f"▶  Tilo API  →  http://{args.host}:{args.port}")
    print(f"   Health     →  http://{args.host}:{args.port}/api/health")
    print(f"   API docs   →  http://{args.host}:{args.port}/docs")
    print()

    uvicorn.run(
        "tilo.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def _init(args: argparse.Namespace) -> None:
    """Scaffold a complete, immediately-runnable Tilo project."""
    name = args.name
    root = Path(name)
    if root.exists():
        print(f"Directory '{name}' already exists.")
        sys.exit(1)

    root.mkdir(parents=True)

    # .env
    (root / ".env").write_text(
        "# Tilo environment\n"
        "# SQLite is used by default — no Docker or Postgres needed.\n"
        "DATABASE_URL=sqlite:///tilo.db\n"
        "\n"
        "# Set LLM_ENABLED=true and add your API key to use real LLM generation.\n"
        "LLM_ENABLED=false\n"
        "LLM_PROVIDER=openai\n"
        "# LLM_API_KEY=sk-...\n"
        "# DEFAULT_MODEL=gpt-4o\n"
    )

    # requirements.txt
    (root / "requirements.txt").write_text(
        "tilo\n"
        "# Add your LLM SDK:\n"
        "# openai\n"
        "# anthropic\n"
        "# langchain-openai\n"
    )

    # hello.py — a complete end-to-end demo script
    (root / "hello.py").write_text(
        '"""Hello Tilo — end-to-end example.\n\n'
        "Run:\n"
        "    1. tilo serve          (keep running in another terminal)\n"
        "    2. python hello.py     (sends a message, prints the AIP spec)\n"
        '"""\n'
        "\n"
        "import json\n"
        "import urllib.request\n"
        "\n"
        "BASE = \"http://127.0.0.1:8000\"\n"
        "\n"
        "\n"
        "def post(path: str, body: dict) -> dict:\n"
        "    data = json.dumps(body).encode()\n"
        "    req = urllib.request.Request(\n"
        "        f\"{BASE}{path}\",\n"
        "        data=data,\n"
        "        headers={\"Content-Type\": \"application/json\"},\n"
        "    )\n"
        "    with urllib.request.urlopen(req) as resp:\n"
        "        return json.loads(resp.read())\n"
        "\n"
        "\n"
        "def main() -> None:\n"
        "    # 1. Create a conversation session\n"
        "    session = post(\"/api/conversations\", {\n"
        "        \"app_id\": \"contract-review-agent\",\n"
        "        \"workspace_id\": \"demo-workspace\",\n"
        "        \"channel\": \"web\",\n"
        "    })\n"
        "    session_id = session[\"id\"]\n"
        "    print(f\"Session: {session_id}\")\n"
        "\n"
        "    # 2. Send a message — triggers the full ROAM loop\n"
        "    result = post(f\"/api/conversations/{session_id}/messages\", {\n"
        "        \"content\": \"Review this SaaS contract and flag any risks.\",\n"
        "        \"attachments\": [],\n"
        "    })\n"
        "    print(f\"\\nRun status: {result.get('run', {}).get('status', 'unknown')}\")\n"
        "\n"
        "    # 3. Fetch the generated artifact (AIP spec)\n"
        "    run_id = result.get(\"run\", {}).get(\"id\")\n"
        "    if run_id:\n"
        "        req = urllib.request.Request(f\"{BASE}/api/artifacts?run_id={run_id}\")\n"
        "        with urllib.request.urlopen(req) as resp:\n"
        "            artifacts = json.loads(resp.read())\n"
        "        if artifacts:\n"
        "            spec = artifacts[0].get(\"spec\", {})\n"
        "            print(f\"\\nArtifact: {spec.get('title', 'untitled')}\")\n"
        "            print(f\"Blocks:   {len(spec.get('blocks', []))}\")\n"
        "            print(\"\\nRender with @adam2go/tilo-react:\")\n"
        "            print(\"  import { renderArtifactBlock } from '@adam2go/tilo-react'\")\n"
        "            for block in spec.get(\"blocks\", [])[:3]:\n"
        "                print(f\"  · [{block['type']}] {block.get('title') or ''}\")\n"
        "\n"
        "\n"
        "if __name__ == \"__main__\":\n"
        "    main()\n"
    )

    # openai_agent.py — optional LLM integration demo
    (root / "openai_agent.py").write_text(
        '"""OpenAI → Tilo AIP example.\n\n'
        "Shows how to convert any OpenAI response into a renderable Tilo surface.\n"
        "Requires: pip install openai\n"
        '"""\n'
        "\n"
        "# from openai import OpenAI\n"
        "# from tilo.adapters.openai import tilo_spec_from_completion\n"
        "# from tilo.schemas.artifact import ArtifactSpecV1\n"
        "#\n"
        "# client = OpenAI()  # reads OPENAI_API_KEY from env\n"
        "#\n"
        "# response = client.chat.completions.create(\n"
        "#     model=\"gpt-4o\",\n"
        "#     messages=[{\"role\": \"user\", \"content\": \"Give me a Q3 revenue summary in JSON\"}],\n"
        "#     response_format={\"type\": \"json_object\"},\n"
        "# )\n"
        "#\n"
        "# spec = tilo_spec_from_completion(response, title=\"Q3 Revenue\")\n"
        "# validated = ArtifactSpecV1.model_validate(spec)  # type-safe\n"
        "# print(f\"Blocks: {[b.type for b in validated.blocks]}\")\n"
        "# # → Render spec with @adam2go/tilo-react\n"
        "\n"
        "print(\"Uncomment the code above and set OPENAI_API_KEY to run this example.\")\n"
    )

    # README.md
    (root / "README.md").write_text(
        f"# {name}\n\n"
        "A [Tilo](https://github.com/adam2go/tilo-framework)-powered AI agent project.\n\n"
        "## Quick start\n\n"
        "```bash\n"
        "# 1. Install dependencies\n"
        "pip install -r requirements.txt\n\n"
        "# 2. Start the Tilo API server (SQLite, no Docker needed)\n"
        "tilo serve\n\n"
        "# 3. In a new terminal, run the demo script\n"
        "python hello.py\n"
        "```\n\n"
        "## Render surfaces in React\n\n"
        "```bash\n"
        "npm install @adam2go/tilo-react recharts lucide-react\n"
        "```\n\n"
        "```tsx\n"
        "import { TiloRenderer, createTiloClient, useTiloSurface } from '@adam2go/tilo-react';\n\n"
        "const client = createTiloClient({ baseUrl: 'http://localhost:8000' });\n\n"
        "function App({ runId }: { runId: string }) {\n"
        "  const { turns } = useTiloSurface({ client, runId });\n"
        "  return <div>{turns.map(t => <TiloRenderer key={t.id} surface={t.spec} />)}</div>;\n"
        "}\n"
        "```\n\n"
        "## With OpenAI\n\n"
        "See `openai_agent.py` for a complete example.\n\n"
        "## Links\n\n"
        "- [Tilo Framework](https://github.com/adam2go/tilo-framework)\n"
        "- [Docs](https://github.com/adam2go/tilo-framework/tree/main/docs)\n"
        "- [npm: @adam2go/tilo-react](https://www.npmjs.com/package/@adam2go/tilo-react)\n"
        "- [PyPI: tilo](https://pypi.org/project/tilo/)\n"
    )

    print(f"✓ Created '{name}/'")
    print()
    print("  Files:")
    print(f"    {name}/.env             — environment config (SQLite by default)")
    print(f"    {name}/requirements.txt — dependencies")
    print(f"    {name}/hello.py         — end-to-end demo script")
    print(f"    {name}/openai_agent.py  — OpenAI integration example")
    print(f"    {name}/README.md        — project docs")
    print()
    print("  Next steps:")
    print(f"    cd {name}")
    print("    pip install -r requirements.txt")
    print("    tilo serve")
    print("    # (new terminal)")
    print("    python hello.py")


def _version() -> None:
    try:
        from importlib.metadata import version
        v = version("tilo")
    except Exception:
        v = "0.1.0 (dev)"
    print(f"tilo {v}")


if __name__ == "__main__":
    main()
