from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.agent_context import AgentContextBuilder
from app.services.apps import AgentAppManifest
from app.services.apps.loader import get_app_loader
from app.services.interaction_policy.schemas import InteractionContext, InteractionDecision
from app.services.interaction_policy.service import InteractionPolicyService

router = APIRouter(prefix="/api/apps", tags=["apps"])


class AgentContextBuildRequest(BaseModel):
    workspace_id: str
    project_id: str | None = None
    artifact_id: str | None = None
    policy_context: InteractionContext | None = None


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
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{app_id}/agent-context")
def build_agent_context(app_id: str, payload: AgentContextBuildRequest, db: Session = Depends(get_db)) -> dict:
    try:
        get_app_loader().load_manifest(app_id)
        return AgentContextBuilder(db).build(
            app_id=app_id,
            workspace_id=payload.workspace_id,
            project_id=payload.project_id,
            artifact_id=payload.artifact_id,
            policy_context=payload.policy_context,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
