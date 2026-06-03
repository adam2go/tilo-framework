"""Surface composition (Phase 2 of the Surface Protocol refactor).

Composers translate `(intent, plan step, context)` into a fully validated
`SurfaceSpec`. See docs/REFACTOR_BLUEPRINT.md ADR-7.
"""

from tilo.services.surface.composer import (
    ComposedSurface,
    ComposerInput,
    DeterministicSurfaceComposer,
    SurfaceComposer,
    safe_compose,
)
from tilo.services.surface.persistence import SurfaceTurnService

__all__ = [
    "ComposedSurface",
    "ComposerInput",
    "DeterministicSurfaceComposer",
    "SurfaceComposer",
    "SurfaceTurnService",
    "safe_compose",
]
