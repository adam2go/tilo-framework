"""Tilo CLI — lightweight entry points for the framework.

Usage after `pip install tilo`:

    tilo serve          Start the API server (uvicorn)
    tilo serve --port 9000
    tilo init myproject  Scaffold a new Tilo project directory
    tilo version        Print version and exit
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="tilo",
        description="Tilo — AI-native SaaS agent framework",
    )
    sub = parser.add_subparsers(dest="command")

    # tilo serve
    serve_p = sub.add_parser("serve", help="Start the Tilo API server")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=8000)
    serve_p.add_argument("--reload", action="store_true", default=False)

    # tilo init
    init_p = sub.add_parser("init", help="Scaffold a new Tilo project")
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

    uvicorn.run(
        "tilo.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def _init(args: argparse.Namespace) -> None:
    """Scaffold a minimal Tilo project directory."""
    name = args.name
    root = Path(name)
    if root.exists():
        print(f"Directory '{name}' already exists.")
        sys.exit(1)

    root.mkdir(parents=True)
    (root / ".env").write_text(
        "# Tilo configuration\n"
        "DATABASE_URL=sqlite:///tilo.db\n"
        "LLM_ENABLED=false\n"
        "# LLM_PROVIDER=openai\n"
        "# LLM_API_KEY=sk-...\n"
        "# DEFAULT_MODEL=gpt-4o\n"
    )
    (root / "README.md").write_text(
        f"# {name}\n\n"
        "A Tilo-powered AI agent project.\n\n"
        "## Quick start\n\n"
        "```bash\n"
        "pip install tilo\n"
        "cd " + name + "\n"
        "tilo serve\n"
        "```\n"
    )
    print(f"✓ Created '{name}/'")
    print(f"  cd {name} && tilo serve")


def _version() -> None:
    try:
        from importlib.metadata import version
        v = version("tilo")
    except Exception:
        v = "0.1.0 (dev)"
    print(f"tilo {v}")


if __name__ == "__main__":
    main()
