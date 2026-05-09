from fastapi import APIRouter
from pydantic import BaseModel

from app.services.demo import load_problematic_ai_service_agreement

router = APIRouter(prefix="/api/demo", tags=["demo"])


class DemoContractRead(BaseModel):
    slug: str
    file_name: str
    title: str
    content: str
    source_path: str


@router.get("/contracts/problematic-ai-service-agreement", response_model=DemoContractRead)
def read_problematic_ai_service_agreement() -> DemoContractRead:
    return DemoContractRead.model_validate(load_problematic_ai_service_agreement().__dict__)
