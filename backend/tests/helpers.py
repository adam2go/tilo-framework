import os
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

db_path = Path(tempfile.gettempdir()) / "tilo_smoke_test.db"
if db_path.exists():
    db_path.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
os.environ["LLM_ENABLED"] = "false"
os.environ["LLM_PROVIDER"] = "openai"
os.environ["LLM_BASE_URL"] = ""
os.environ["OPENAI_API_KEY"] = ""

from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Artifact, Confirmation, ContextReflection, ConversationSession, ConversationTurn, Memory, Run, Task, Tool, TraceStep, UIInteractionEvent  # noqa: E402
from app.services.agent_context import AgentContextBuilder  # noqa: E402
from app.services.agent_runtime.run_manager import RunManager  # noqa: E402
from app.services.agent_runtime.prompt_builder import PromptBuilder  # noqa: E402
from app.services.agent_runtime.state_machine import InvalidStateTransition, RunStateMachine  # noqa: E402
from app.services.artifact.generator import ArtifactGenerator  # noqa: E402
from app.services.artifact.spec import ArtifactSpecBuilder  # noqa: E402
from app.services.channels.telegram.adapter import TelegramAdapter  # noqa: E402
from app.services.channels.telegram.types import parse_telegram_callback_data  # noqa: E402
from app.services.artifact.contract_llm import ContractReviewLLMGenerator  # noqa: E402
from app.services.models.client import ModelClient  # noqa: E402
from app.services.models.errors import ModelDisabledError, ModelInvalidJSONError  # noqa: E402
from app.services.demo import load_problematic_ai_service_agreement  # noqa: E402
from app.services.apps.loader import AgentAppLoader, get_app_loader  # noqa: E402
from app.services.conversations.constants import ConversationChannel, ConversationTurnType  # noqa: E402
from app.services.conversations.service import ConversationService  # noqa: E402
from app.services.context_reflection import ContextReflectionService  # noqa: E402
from app.services.interaction_policy.schemas import InteractionContext, InteractionDecisionType  # noqa: E402
from app.services.interaction_policy.service import InteractionPolicyService  # noqa: E402
from app.schemas import RichSurfaceLink  # noqa: E402
from app.schemas.artifact import CORE_BLOCK_TYPES, ArtifactSpecV1  # noqa: E402
from app.services.surfaces.constants import RichSurfaceSource, RichSurfaceTargetType  # noqa: E402
from app.services.surfaces.rich_links import create_rich_surface_link  # noqa: E402
from app.services.trace.recorder import TraceRecorder  # noqa: E402


def create_action_artifact(
    *,
    workspace_id: str,
    actions: list[dict] | None = None,
    blocks: list[dict] | None = None,
    run_id: str | None = None,
) -> str:
    with SessionLocal() as db:
        artifact = Artifact(
            workspace_id=workspace_id,
            run_id=run_id,
            title="Action Runtime Artifact",
            type="contract_review",
            schema_json={
                "version": "artifact_spec.v1",
                "artifact_type": "contract_review",
                "title": "Action Runtime Artifact",
                "status": "ready",
                "blocks": blocks
                or [
                    {
                        "id": "summary",
                        "type": "approval_card",
                        "data": {"title": "Approve"},
                        "actions": [
                            {
                                "id": "approve_block",
                                "label": "Approve block",
                                "action_type": "approve",
                                "confirmation_required": False,
                            }
                        ],
                    }
                ],
                "actions": actions or [],
                "run_id": run_id,
            },
        )
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        return artifact.id
