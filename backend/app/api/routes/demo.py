from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings
from app.services.demo import FollowUpIntentClassifier, load_problematic_ai_service_agreement

router = APIRouter(prefix="/api/demo", tags=["demo"])


class DemoContractRead(BaseModel):
    slug: str
    file_name: str
    title: str
    content: str
    source_path: str


class FollowUpIntentCreate(BaseModel):
    text: str
    locale: str = "en"
    artifact_id: str | None = None
    run_id: str | None = None


class FollowUpIntentRead(BaseModel):
    intent: str
    confidence: float
    mode: str
    reason: str


@router.get("/contracts/problematic-ai-service-agreement", response_model=DemoContractRead)
def read_problematic_ai_service_agreement() -> DemoContractRead:
    return DemoContractRead.model_validate(load_problematic_ai_service_agreement().__dict__)


@router.post("/followup-intent", response_model=FollowUpIntentRead)
def classify_followup_intent(payload: FollowUpIntentCreate) -> FollowUpIntentRead:
    result = FollowUpIntentClassifier(get_settings()).classify(payload.text, payload.locale)
    return FollowUpIntentRead.model_validate(result.model_dump())
