from fastapi import APIRouter, HTTPException

from app.services.apps import AgentAppManifest
from app.services.apps.loader import get_app_loader
from app.services.interaction_policy.schemas import InteractionContext, InteractionDecision
from app.services.interaction_policy.service import InteractionPolicyService

router = APIRouter(prefix="/api/apps", tags=["apps"])


@router.get("", response_model=list[AgentAppManifest])
def list_apps() -> list[AgentAppManifest]:
    return get_app_loader().list_apps()


@router.get("/{app_id}", response_model=AgentAppManifest)
def read_app(app_id: str) -> AgentAppManifest:
    try:
        return get_app_loader().load_manifest(app_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{app_id}/interaction-policy/evaluate", response_model=InteractionDecision)
def evaluate_app_interaction_policy(app_id: str, context: InteractionContext) -> InteractionDecision:
    try:
        return InteractionPolicyService().evaluate_for_app(app_id, context)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
