"""AIP v1 LLM-driven artifact spec generation.

Replaces the 924-line deterministic ArtifactSpecBuilder with an LLM-first
approach. The LLM receives:
  - The user's goal
  - Available primitive block types
  - Skill hints (if a skill is active)
  - Memory snippets

It generates a complete { views, blocks } spec. A deterministic fallback
is used when LLM is unavailable or returns invalid output.

See docs/AIP_DESIGN.md §7 for full design rationale.
"""

from typing import Any

from pydantic import ValidationError

from tilo.models import Memory, Run, Task
from tilo.schemas.artifact import ArtifactSpecV1, PRIMITIVE_BLOCK_TYPES
from tilo.services.models.client import ModelClient
from tilo.services.models.errors import ModelClientError


# --------------------------------------------------------------------------- #
# Prompt construction                                                          #
# --------------------------------------------------------------------------- #

_BLOCK_TYPE_REFERENCE = """Available Tilo AIP block types (use these as block "type" values):

Content display:
  - markdown: Rich text content (supports full markdown syntax)
  - table: Data table with columns and rows. props: {columns: [{key, label}], rows: [{...}]}
  - list: Ordered or unordered items. props: {items: [{text, severity?}], ordered?: bool}
  - image: Image with alt text. props: {src, alt, caption?}
  - code: Code block. props: {content, language?}
  - heading: Section heading. props: {text, level?: 1-6}

Data visualization:
  - metric: KPI card. props: {label, value, delta?, trend?}
  - chart: Visualization. props: {chart_type: "bar"|"line"|"pie"|"radar", data: {...}}
  - progress: Progress indicator. props: {percent?, steps?: [{label, state}]}

User interaction:
  - form: Input fields. props: {fields: [{name, label, kind}], submit_action_id}
  - button_group: Action buttons. props: {buttons: [{label, action_id}]}

Structured display:
  - card: Container with title/content. props: {title?, content, severity?, status?}
  - diff: Before/after comparison. props: {before, after, context?}
  - timeline: Chronological events. props: {items: [{time, title, description}]}
  - kanban: Board columns. props: {columns: [{title, cards: [{title, description}]}]}

Framework-specific:
  - confirmation: Requires human approval. props: {title, description, risk_level?}
  - memory_card: Memory candidate. props: {content, memory_type?, confidence?}
  - tool_preview: Tool call preview. props: {tool_name, summary, permission_level?}

You may also use custom block types (any string). Unknown types will render
as a generic JSON viewer on the frontend — this is fine for domain-specific blocks.
"""

_SYSTEM_PROMPT = f"""You are the Tilo AIP artifact spec generator.

Your job: given a user goal, generate a complete interactive artifact specification
as a JSON object. The artifact will be rendered as an interactive Canvas with
tabbed views containing typed blocks.

{_BLOCK_TYPE_REFERENCE}

Output format — return this exact JSON structure:
{{
  "title": "Human-readable artifact title",
  "views": [
    {{
      "id": "unique_view_id",
      "label": "Tab label",
      "icon": "lucide-icon-name or null",
      "description": "Optional one-liner",
      "block_ids": ["block_id_1", "block_id_2"]
    }}
  ],
  "blocks": [
    {{
      "id": "unique_block_id",
      "type": "one of the block types above",
      "title": "Block title or null",
      "props": {{ ... type-specific properties ... }},
      "actions": []
    }}
  ],
  "follow_ups": ["suggested follow-up question 1", "suggested follow-up question 2"],
  "memory_candidate": {{
    "content": "What to remember about the user's preference",
    "memory_type": "preference",
    "confidence": 0.7
  }}
}}

Rules:
1. Generate 2-4 views (tabs) that organize the analysis logically.
2. Generate 4-10 blocks covering the analysis comprehensively.
3. Every block referenced in a view's block_ids must exist in the blocks array.
4. Use the most appropriate block type for each piece of content.
5. Generate 2-3 contextual follow-up questions in follow_ups.
6. Match output language to the user's language.
7. Include actions on blocks where user interaction makes sense (approve, reject, edit, select).
8. Return ONLY valid JSON. No markdown, no commentary.
"""


def _build_user_prompt(
    task_message: str,
    memory_snippets: list[str],
    skill_hints: str | None = None,
    contract_text: str | None = None,
) -> str:
    parts = [f"User goal:\n{task_message}\n"]

    if contract_text:
        parts.append(
            "\nFull document text:\n"
            "---BEGIN DOCUMENT---\n"
            f"{contract_text}\n"
            "---END DOCUMENT---\n"
        )

    if memory_snippets:
        parts.append(f"\nRecalled memories:\n{memory_snippets[:5]}\n")

    if skill_hints:
        parts.append(f"\nSkill hints (recommendations, not requirements):\n{skill_hints}\n")

    parts.append(
        "\nGenerate the complete artifact spec JSON now. "
        "Organize views and blocks based on the user's actual goal."
    )
    return "".join(parts)


# --------------------------------------------------------------------------- #
# Skill hints (built-in for the 3 demo scenarios)                             #
# --------------------------------------------------------------------------- #

_DEMO_SKILL_HINTS: dict[str, str] = {
    "contract_review": """For contract review tasks, consider:
- chart(radar) for risk distribution across categories (liability, payment, IP, etc.)
- card blocks for risk summary with severity counts
- table for detailed risk findings (clause, severity, issue, suggestion)
- diff for revision suggestions (before/after text)
- markdown for clause reading with full contract text
- memory_card for user preference memory

Recommended views:
- "Risks" tab: risk overview chart + risk summary card + risk findings table
- "Clauses" tab: full contract text with risk-linked clause highlights
- "Revision" tab: diff blocks showing suggested changes
- "Memory" tab: memory candidate card
""",

    "sales_dashboard": """For sales follow-up tasks, consider:
- metric blocks for pipeline KPIs (hot accounts, projected pipeline, pending decisions)
- card for key insights
- list for recommended action items with status
- tool_preview for outbound action preview

Recommended views:
- "Pipeline" tab: metric blocks + insights
- "Actions" tab: action item list + tool preview
""",

    "competitive_analysis": """For competitive analysis tasks, consider:
- table for comparison matrix (company, positioning, strength, gap)
- markdown for analysis summary
- list for recommended next steps

Recommended views:
- "Comparison" tab: comparison table + summary
- "Next Steps" tab: action items list
""",
}


def _detect_skill_hint(message: str) -> str | None:
    """Simple keyword-based skill hint detection for demo scenarios."""
    text = message.lower()
    if any(w in text for w in ["contract", "clause", "agreement", "nda", "合同", "条款"]):
        return _DEMO_SKILL_HINTS["contract_review"]
    if any(w in text for w in ["sales", "customer", "crm", "follow", "客户", "跟进"]):
        return _DEMO_SKILL_HINTS["sales_dashboard"]
    if any(w in text for w in ["competitor", "competitive", "market", "竞品", "竞争"]):
        return _DEMO_SKILL_HINTS["competitive_analysis"]
    return None


# --------------------------------------------------------------------------- #
# Main generator                                                               #
# --------------------------------------------------------------------------- #


class AIPSpecGenerator:
    """LLM-driven artifact spec generator with deterministic fallback."""

    def __init__(self, client: ModelClient | None = None):
        self.client = client

    def generate(
        self,
        task: Task,
        run: Run,
        memories: list[Memory],
        tool_outputs: list[dict[str, Any]],
        *,
        contract_text: str | None = None,
        on_thinking: Any = None,
        on_content: Any = None,
    ) -> dict[str, Any]:
        """Generate a complete AIP v1 spec.

        Returns the spec as a dict ready to be stored as schema_json.
        """
        memory_snippets = [m.content for m in memories[:5]]
        memory_refs = [m.id for m in memories]
        skill_hints = _detect_skill_hint(task.input_message)

        # Try LLM generation
        llm_spec = None
        generation_mode = "deterministic"
        follow_ups: list[str] = []
        memory_candidate_data: dict[str, Any] | None = None

        if self.client and self.client.enabled:
            try:
                llm_spec, follow_ups, memory_candidate_data = self._call_llm(
                    task.input_message,
                    memory_snippets,
                    skill_hints=skill_hints,
                    contract_text=contract_text,
                    on_thinking=on_thinking,
                    on_content=on_content,
                )
                generation_mode = "llm"
            except (ModelClientError, ValidationError, ValueError, KeyError, TypeError):
                llm_spec = None

        if llm_spec is not None:
            # LLM returned a valid spec — enrich with runtime metadata
            llm_spec["version"] = "tilo/aip/v1"
            llm_spec["status"] = "ready"
            llm_spec["provenance"] = [{"type": "task", "id": task.id, "label": task.title}]
            llm_spec["memory_refs"] = memory_refs
            llm_spec["run_id"] = run.id
            if follow_ups:
                llm_spec["follow_ups"] = follow_ups[:3]
            # Validate the full spec
            try:
                spec = ArtifactSpecV1.model_validate(llm_spec)
                result = spec.model_dump(mode="json")
                result["_generation_mode"] = generation_mode
                result["_memory_candidate"] = memory_candidate_data
                return result
            except ValidationError:
                pass  # Fall through to deterministic

        # Deterministic fallback
        return self._deterministic_fallback(
            task, run, memory_refs, memory_snippets, skill_hints,
        )

    def _call_llm(
        self,
        task_message: str,
        memory_snippets: list[str],
        *,
        skill_hints: str | None,
        contract_text: str | None,
        on_thinking: Any,
        on_content: Any,
    ) -> tuple[dict[str, Any], list[str], dict[str, Any] | None]:
        """Call LLM and parse the response.

        Returns (spec_dict, follow_ups, memory_candidate_data).
        """
        user_prompt = _build_user_prompt(
            task_message, memory_snippets,
            skill_hints=skill_hints,
            contract_text=contract_text,
        )

        if hasattr(self.client, "chat_json_streaming_sync"):
            raw = self.client.chat_json_streaming_sync(
                system=_SYSTEM_PROMPT,
                user=user_prompt,
                schema_name="aip_spec",
                temperature=0.3,
                on_thinking=on_thinking,
                on_content=on_content,
            )
        else:
            raw = self.client.chat_json_sync(
                system=_SYSTEM_PROMPT,
                user=user_prompt,
                schema_name="aip_spec",
                temperature=0.3,
            )

        # Extract follow_ups and memory_candidate before they get validated
        follow_ups = raw.pop("follow_ups", []) if isinstance(raw, dict) else []
        memory_candidate = raw.pop("memory_candidate", None) if isinstance(raw, dict) else None

        # Normalize blocks: ensure "props" field exists
        if isinstance(raw, dict) and "blocks" in raw:
            for block in raw["blocks"]:
                if isinstance(block, dict) and "data" in block and "props" not in block:
                    block["props"] = block.pop("data")

        return raw, follow_ups, memory_candidate

    @staticmethod
    def _deterministic_fallback(
        task: Task,
        run: Run,
        memory_refs: list[str],
        memory_snippets: list[str],
        skill_hints: str | None,
    ) -> dict[str, Any]:
        """Generate a simple but valid spec without LLM."""
        zh = any("\u4e00" <= ch <= "\u9fff" for ch in task.input_message[:200])
        memory_note = f"\n\n已召回记忆: {memory_snippets[0]}" if zh and memory_snippets else (
            f"\n\nRecalled memory: {memory_snippets[0]}" if memory_snippets else ""
        )

        spec = ArtifactSpecV1(
            version="tilo/aip/v1",
            artifact_type="document",
            title="分析结果" if zh else "Analysis Result",
            blocks=[
                {
                    "id": "summary",
                    "type": "markdown",
                    "title": "摘要" if zh else "Summary",
                    "props": {"content": f"{task.input_message}{memory_note}"},
                },
            ],
            provenance=[{"type": "task", "id": task.id, "label": task.title}],
            memory_refs=memory_refs,
            run_id=run.id,
        )
        result = spec.model_dump(mode="json")
        result["_generation_mode"] = "deterministic"
        result["_memory_candidate"] = None
        return result


# --------------------------------------------------------------------------- #
# Slim ArtifactTypeDetector (kept for backward compat, used by generator.py)  #
# --------------------------------------------------------------------------- #

class ArtifactTypeDetector:
    """Simple keyword-based type detector. Used only for trace/logging."""

    def detect(self, message: str) -> str:
        text = message.lower()
        if any(w in text for w in ["contract", "clause", "agreement", "nda", "合同", "条款"]):
            return "contract_review"
        if any(w in text for w in ["sales", "customer", "crm", "follow", "客户", "跟进"]):
            return "dashboard"
        if any(w in text for w in ["competitor", "competitive", "market", "竞品", "竞争"]):
            return "table"
        return "document"
