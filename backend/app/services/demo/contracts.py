from dataclasses import dataclass
from pathlib import Path


SAMPLE_CONTRACT_SLUG = "problematic-ai-service-agreement"
SAMPLE_CONTRACT_FILE_NAME = "AI 客服系统定制开发与运维服务合同（问题样例）.md"


@dataclass(frozen=True)
class DemoContractFixture:
    slug: str
    file_name: str
    title: str
    content: str
    source_path: str


def load_problematic_ai_service_agreement() -> DemoContractFixture:
    path = _find_contract_fixture()
    content = path.read_text(encoding="utf-8")
    title = content.splitlines()[0].lstrip("# ").strip() if content else SAMPLE_CONTRACT_FILE_NAME
    return DemoContractFixture(
        slug=SAMPLE_CONTRACT_SLUG,
        file_name=SAMPLE_CONTRACT_FILE_NAME,
        title=title,
        content=content,
        source_path="examples/contracts/problematic-ai-service-agreement.md",
    )


def _find_contract_fixture() -> Path:
    current = Path(__file__).resolve()
    candidates = [
        current.parents[4] / "examples/contracts/problematic-ai-service-agreement.md",
        current.parents[3] / "examples/contracts/problematic-ai-service-agreement.md",
        Path.cwd() / "examples/contracts/problematic-ai-service-agreement.md",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("examples/contracts/problematic-ai-service-agreement.md")
