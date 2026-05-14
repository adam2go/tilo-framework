"""Export the Tilo Surface Protocol JSON Schema.

Reads the Pydantic models in `backend/app/schemas/surface.py` and writes a
JSON Schema file consumable by non-Python renderers (TypeScript, Go, etc).

Usage:
    python scripts/export_surface_schema.py            # write file
    python scripts/export_surface_schema.py --check    # exit 1 if file is stale
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
OUTPUT_FILE = REPO_ROOT / "frontend" / "lib" / "surface.schema.json"

# Make `app.*` imports resolve.
sys.path.insert(0, str(BACKEND_DIR))

from tilo.schemas.surface import SurfaceSpecV1  # noqa: E402  (import after sys.path mutation)


def build_schema() -> dict:
    schema = SurfaceSpecV1.model_json_schema(mode="serialization")
    # Stamp a comment for humans reading the file.
    schema["$comment"] = (
        "Generated from backend/app/schemas/surface.py via "
        "scripts/export_surface_schema.py. Do not edit by hand."
    )
    return schema


def serialize(schema: dict) -> str:
    return json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Tilo Surface Protocol JSON Schema")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if the on-disk schema differs from the generated one.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_FILE,
        help=f"Output path (default: {OUTPUT_FILE.relative_to(REPO_ROOT)})",
    )
    args = parser.parse_args()

    schema_text = serialize(build_schema())

    if args.check:
        if not args.output.exists():
            print(f"[FAIL] {args.output} does not exist; run without --check first.", file=sys.stderr)
            return 1
        existing = args.output.read_text(encoding="utf-8")
        if existing != schema_text:
            print(
                f"[FAIL] {args.output} is out of date. Run: python scripts/export_surface_schema.py",
                file=sys.stderr,
            )
            return 1
        print(f"[OK] {args.output.relative_to(REPO_ROOT)} is up to date.")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(schema_text, encoding="utf-8")
    print(f"[OK] wrote {args.output.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
