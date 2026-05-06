from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.services.apps.schemas import AgentAppManifest


class AgentAppLoader:
    def __init__(self, apps_root: Path | None = None) -> None:
        self.apps_root = apps_root or repo_root() / "examples" / "apps"

    def list_apps(self) -> list[AgentAppManifest]:
        if not self.apps_root.exists():
            return []
        apps: list[AgentAppManifest] = []
        for path in sorted(self.apps_root.glob("*/app.yaml")):
            apps.append(self.load_manifest(path.parent.name))
        return apps

    def load_manifest(self, app_id: str) -> AgentAppManifest:
        app_dir = self._safe_app_dir(app_id)
        manifest = self._read_yaml(app_dir / "app.yaml")
        app = AgentAppManifest.model_validate(manifest)
        if app.id != app_id:
            raise ValueError(f"Manifest id {app.id!r} does not match app directory {app_id!r}")
        return app.model_copy(update={"sample_inputs": [self._resolve_sample_input(item, app_dir) for item in app.sample_inputs]})

    def load_policy_path(self, app_id: str) -> Path:
        app = self.load_manifest(app_id)
        return self._resolve_app_file(self._safe_app_dir(app_id), app.runtime.interaction_policy)

    def _safe_app_dir(self, app_id: str) -> Path:
        app_dir = (self.apps_root / app_id).resolve()
        apps_root = self.apps_root.resolve()
        if apps_root not in app_dir.parents and app_dir != apps_root:
            raise ValueError("App id resolves outside examples/apps")
        if not app_dir.exists():
            raise FileNotFoundError(f"Unknown app: {app_id}")
        return app_dir

    def _resolve_sample_input(self, item, app_dir: Path):
        resolved = self._resolve_sample_file(app_dir, item.path)
        return item.model_copy(update={"resolved_path": str(resolved.relative_to(repo_root()))})

    def _resolve_app_file(self, app_dir: Path, relative_path: str) -> Path:
        resolved = (app_dir / relative_path).resolve()
        if app_dir.resolve() not in resolved.parents and resolved != app_dir.resolve():
            raise ValueError(f"Path resolves outside app directory: {relative_path}")
        if not resolved.exists():
            raise FileNotFoundError(relative_path)
        return resolved

    def _resolve_sample_file(self, app_dir: Path, relative_path: str) -> Path:
        resolved = (app_dir / relative_path).resolve()
        allowed_contracts = (repo_root() / "examples" / "contracts").resolve()
        allowed_fixtures = (repo_root() / "examples" / "fixtures").resolve()
        app_dir = app_dir.resolve()
        is_inside_app = app_dir in resolved.parents or resolved == app_dir
        is_contract_fixture = allowed_contracts in resolved.parents or resolved == allowed_contracts
        is_shared_fixture = allowed_fixtures in resolved.parents or resolved == allowed_fixtures
        if not is_inside_app and not is_contract_fixture and not is_shared_fixture:
            raise ValueError(f"Sample input must be inside the app directory, examples/contracts, or examples/fixtures: {relative_path}")
        if not resolved.exists():
            raise FileNotFoundError(relative_path)
        return resolved

    @staticmethod
    def _read_yaml(path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        if not isinstance(data, dict):
            raise ValueError(f"Expected mapping in {path}")
        return data


@lru_cache
def get_app_loader() -> AgentAppLoader:
    return AgentAppLoader()


def repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "examples").exists() and ((parent / "backend").exists() or (parent / "pyproject.toml").exists()):
            return parent
    return current.parents[4]
