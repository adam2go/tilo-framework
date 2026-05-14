from typing import Any

from tilo.schemas import RichSurfaceLink, RichSurfaceTarget
from tilo.services.surfaces.constants import RichSurfaceSource, RichSurfaceTargetType


def create_rich_surface_link(
    *,
    surface: str,
    title: str,
    target_type: RichSurfaceTargetType,
    source: RichSurfaceSource,
    artifact_id: str | None = None,
    url: str | None = None,
    target_title: str | None = None,
    channel: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> RichSurfaceLink:
    return RichSurfaceLink(
        surface=surface,
        title=title,
        target=RichSurfaceTarget(
            type=target_type,
            artifactId=artifact_id,
            url=url,
            title=target_title,
            source=source,
        ),
        channel=channel,
        metadata=metadata or {},
    )
