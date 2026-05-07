#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml


SECRET_KEY_RE = re.compile(r"(api[_-]?key|token|secret|password|authorization|private[_-]?key)", re.IGNORECASE)
SECRET_VALUE_RE = re.compile(r"(sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9_]{16,}|xox[baprs]-[A-Za-z0-9-]{12,})")
REQUIRED_MANIFEST_FIELDS = ("id", "version", "name", "description", "entry", "runtime", "surfaces", "sample_inputs", "tools", "channels")


class ValidationError(Exception):
    pass


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] in {"-h", "--help"}:
        print("Usage: python scripts/validate_app.py examples/apps/my-agent")
        return 0 if len(sys.argv) == 2 else 1

    repo_root = Path(__file__).resolve().parents[1]
    app_dir = Path(sys.argv[1]).expanduser()
    if not app_dir.is_absolute():
        app_dir = (repo_root / app_dir).resolve()

    try:
        validate_app(app_dir, repo_root)
    except Exception as exc:
        print(f"✗ app validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


def validate_app(app_dir: Path, repo_root: Path) -> None:
    if not app_dir.exists() or not app_dir.is_dir():
        raise ValidationError(f"app directory not found: {app_dir}")

    manifest_path = app_dir / "app.yaml"
    policy_path = app_dir / "interaction.policy.yaml"
    require_file(manifest_path, "app.yaml")
    print("✓ app.yaml exists")
    require_file(policy_path, "interaction.policy.yaml")
    print("✓ interaction.policy.yaml exists")

    manifest = read_yaml(manifest_path)
    policy = read_yaml(policy_path)
    validate_required_manifest_fields(manifest)
    print("✓ required manifest fields present")
    validate_manifest_shape(manifest)
    print("✓ manifest shape ok")
    validate_policy_surfaces(manifest, policy)
    print("✓ policy surfaces declared")
    validate_sample_paths(manifest, app_dir, repo_root)
    print("✓ sample paths safe")
    validate_no_obvious_secrets(app_dir)
    print("✓ no obvious secrets found")
    print("✓ app validation passed")


def require_file(path: Path, name: str) -> None:
    if not path.exists() or not path.is_file():
        raise ValidationError(f"{name} not found at {path}")


def read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValidationError(f"expected mapping in {path}")
    return data


def validate_required_manifest_fields(manifest: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    if missing:
        raise ValidationError(f"manifest missing required fields: {', '.join(missing)}")


def validate_manifest_shape(manifest: dict[str, Any]) -> None:
    entry = manifest.get("entry")
    runtime = manifest.get("runtime")
    surfaces = manifest.get("surfaces")
    if not isinstance(entry, dict) or entry.get("type") != "conversation" or not entry.get("default_prompt"):
        raise ValidationError("entry must be a conversation entry with default_prompt")
    if not isinstance(runtime, dict) or not runtime.get("interaction_policy"):
        raise ValidationError("runtime.interaction_policy is required")
    if not isinstance(surfaces, dict):
        raise ValidationError("surfaces must contain mini and rich lists")
    for key in ("mini", "rich"):
        if not isinstance(surfaces.get(key), list):
            raise ValidationError(f"surfaces.{key} must be a list")
    for key in ("sample_inputs", "tools", "channels"):
        if not isinstance(manifest.get(key), list):
            raise ValidationError(f"{key} must be a list")


def validate_policy_surfaces(manifest: dict[str, Any], policy: dict[str, Any]) -> None:
    rules = policy.get("rules")
    if not isinstance(rules, list):
        raise ValidationError("policy.rules must be a list")
    declared_mini = set(str(item) for item in manifest.get("surfaces", {}).get("mini", []))
    declared_rich = set(str(item) for item in manifest.get("surfaces", {}).get("rich", []))
    for rule in rules:
        if not isinstance(rule, dict):
            raise ValidationError("each policy rule must be a mapping")
        decision = rule.get("decision")
        surface = rule.get("surface")
        if decision == "mini_surface" and surface not in declared_mini:
            raise ValidationError(f"rule {rule.get('id')} references undeclared mini surface {surface}")
        if decision == "rich_surface" and surface not in declared_rich:
            raise ValidationError(f"rule {rule.get('id')} references undeclared rich surface {surface}")


def validate_sample_paths(manifest: dict[str, Any], app_dir: Path, repo_root: Path) -> None:
    allowed_roots = [
        app_dir.resolve(),
        (repo_root / "examples" / "contracts").resolve(),
        (repo_root / "examples" / "fixtures").resolve(),
    ]
    for item in manifest.get("sample_inputs", []):
        if not isinstance(item, dict) or not item.get("path"):
            raise ValidationError("each sample input needs a path")
        resolved = (app_dir / str(item["path"])).resolve()
        if not any(root == resolved or root in resolved.parents for root in allowed_roots):
            raise ValidationError(f"sample path resolves outside allowed fixture roots: {item['path']}")
        if not resolved.exists():
            raise ValidationError(f"sample path does not exist: {item['path']}")


def validate_no_obvious_secrets(app_dir: Path) -> None:
    checked_suffixes = {".yaml", ".yml", ".json", ".md", ".txt"}
    for path in app_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in checked_suffixes:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if SECRET_VALUE_RE.search(line):
                raise ValidationError(f"possible secret value in {path.relative_to(app_dir)}:{line_number}")
            if SECRET_KEY_RE.search(line) and not looks_like_placeholder(line):
                raise ValidationError(f"possible secret key in {path.relative_to(app_dir)}:{line_number}")


def looks_like_placeholder(line: str) -> bool:
    lowered = line.lower()
    return any(token in lowered for token in ("example", "placeholder", "your-", "<", "...", "not required", "empty"))


if __name__ == "__main__":
    raise SystemExit(main())
