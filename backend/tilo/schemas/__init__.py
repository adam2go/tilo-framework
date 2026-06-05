"""Tilo Pydantic schemas — lazily aggregated from the submodules.

Names from `artifact`, `surface`, and `domain` are resolved on first access
via PEP 562 ``__getattr__``. This keeps the lightweight import path
(`import tilo` → `tilo.generate` → `ArtifactSpecV1`) from eagerly loading the
heavy `domain` schemas (54 models + service constants) it doesn't need —
shaving ~50ms off cold-start import time. The server code that uses domain
schemas (`from tilo.schemas import AgentRead`, …) still works; the import is
just deferred to first use.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

# Submodules searched, in priority order, when resolving an attribute.
_SUBMODULES = ("artifact", "surface", "domain")


def __getattr__(name: str) -> Any:  # PEP 562
    for mod_name in _SUBMODULES:
        module = importlib.import_module(f"tilo.schemas.{mod_name}")
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value  # cache so future lookups skip the search
            return value
    raise AttributeError(f"module 'tilo.schemas' has no attribute {name!r}")


if TYPE_CHECKING:  # help type checkers / IDEs resolve the re-exports
    from tilo.schemas.artifact import *  # noqa: F401,F403
    from tilo.schemas.domain import *  # noqa: F401,F403
    from tilo.schemas.surface import *  # noqa: F401,F403
