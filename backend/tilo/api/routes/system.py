from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from tilo.core.config import get_settings
from tilo.core.database import get_db
from tilo.models import Agent, Project, Workspace
from tilo.schemas import BootstrapResponse
from tilo.services.models.client import ModelClient

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/runtime/capabilities")
def runtime_capabilities() -> dict[str, object]:
    settings = get_settings()
    model_capabilities = ModelClient(settings).capabilities()
    llm_available = bool(settings.llm_enabled and model_capabilities["configured"])
    return {
        "llm_enabled": llm_available,
        "llm_configured": model_capabilities["configured"],
        "llm_runtime_mode": "llm" if llm_available else "deterministic",
        "llm_provider": model_capabilities["provider"],
        "llm_provider_family": model_capabilities["provider_family"],
        "llm_supported_providers": model_capabilities["supported_providers"],
        "default_model": settings.default_model,
        "telegram_enabled": bool(settings.telegram_bot_token and settings.telegram_webhook_url),
        "public_app_url": settings.public_app_url,
    }


@router.get("/bootstrap", response_model=BootstrapResponse)
def bootstrap(db: Session = Depends(get_db)) -> dict[str, Any]:
    workspace = db.scalar(select(Workspace).limit(1))
    projects = db.scalars(select(Project).where(Project.workspace_id == workspace.id)).all() if workspace else []
    agents = db.scalars(select(Agent).where(Agent.workspace_id == workspace.id)).all() if workspace else []
    return {"workspace": workspace, "projects": projects, "agents": agents}
