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

_BLOCK_TYPE_REFERENCE = """Block types (use as block "type" value):

Content: markdown {content}, table {columns:[{key,label}], rows:[{...}]}, list {items:[{text,severity?}]}, code {content,language?}

Visualization:
  - metric {label, value, delta?}
  - chart {chart_type:"bar|radar|pie", axes:[{label,score}]}  ← use this simple shape, NOT Chart.js
  - progress {percent}

Structured: card {title?, content, severity?}, diff {before, after, context?}, timeline {items:[{time,title,description}]}

Interaction (PREFER THESE — make the artifact engaging, not just a report):
  - checklist {items:[{text, detail?, checked?:bool}]}  ← user can tick items
  - button_group {buttons:[{label, action_id, variant?:"primary|default"}]}  ← user can click actions
  - rating {label, value:number, max:number}  ← user can change stars
  - form {fields:[{name, label, kind:"text|number"}]}  ← user can fill & submit
  - confirmation {description, risk_level?:"high|medium|low"}  ← human-in-the-loop gate
  - memory_card {content, confidence?:0..1}  ← agent's learned preference

Custom types are fine — unknown types render as JSON viewer.
"""

_SYSTEM_PROMPT = f"""You are the Tilo AIP artifact spec generator. Generate a JSON artifact spec for the user goal.

{_BLOCK_TYPE_REFERENCE}

Output exactly this JSON shape:
{{
  "title": "...",
  "views": [{{ "id": "...", "label": "...", "block_ids": ["..."] }}],
  "blocks": [{{ "id": "...", "type": "...", "title": "...", "props": {{...}} }}],
  "follow_ups": ["...", "..."]
}}

Rules:
1. 2-3 views, 5-7 blocks total. Spread blocks across views.
2. Every view block_id must exist in blocks.
3. For chart: use {{chart_type, axes:[{{label,score}}]}} — NOT labels/datasets.
4. **At least 2 of the blocks MUST be interactive** (checklist, button_group, rating, form, confirmation, memory_card). Don't make it pure read-only.
5. Always include a `memory_card` block at the end with what the agent has learned about the user's preference.
6. Keep content concise: table rows ≤ 5, list/checklist items ≤ 6, markdown ≤ 150 words.
7. **OUTPUT IN ENGLISH ONLY**, regardless of input language. The Canvas demo is English-only.
8. Generate exactly 4 follow_ups that progressively deepen the conversation (e.g. "Refine this with X" → "Now do Y based on the result" → "Compare to Z" → "Save as a template").
9. Return ONLY JSON. No markdown fences, no commentary.

CRITICAL — STAY ON-TOPIC:
10. Every block (title, content, examples) MUST directly serve the user's stated goal.
    Do NOT invent unrelated examples, side-quests, or generic templates.
    - If the user asks about AI framework comparison: every block is about AI frameworks.
    - If the user asks about a contract: every block is about THAT contract.
    - If the user asks about sales pipeline: do NOT add contract diffs or trip plans.
    Bad example (do not do this): user asks "Compare Tilo vs LangChain" and you output a block titled
    "Next Steps for Sales Follow-up" or "Contract Clause Difference Example". These belong to other domains.
11. Block titles must be specific and topical. Generic placeholder titles like "Example", "Demo Block",
    "Sample Data" are forbidden. Reference actual entities from the user's goal in the title when possible.
12. Use ONLY entity names mentioned (or clearly implied) by the user's goal. Do not introduce
    fictional companies, products, or scenarios from other domains.
"""


def _build_user_prompt(
    task_message: str,
    memory_snippets: list[str],
    skill_hints: str | None = None,
    contract_text: str | None = None,
) -> str:
    parts = [
        "User goal (this is the SINGLE topic — every block must serve it):\n"
        f"\"\"\"\n{task_message}\n\"\"\"\n"
    ]

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
        parts.append(
            "\nSkill hints — these are RECOMMENDED block types for this domain. "
            "They suggest structure, NOT content. All content must come from the user goal above:\n"
            f"{skill_hints}\n"
        )

    parts.append(
        "\nGenerate the complete artifact spec JSON now. "
        "Re-read the user goal above and ensure every block title and prop "
        "directly addresses that exact goal. Do not borrow examples from other domains."
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

    "trip_planning": """For trip / travel planning tasks, consider:
- card with destination summary (vibe, best season, must-knows)
- timeline for day-by-day itinerary
- checklist for packing list or pre-departure tasks (interactive!)
- table for hotel/restaurant comparison (name, area, price, rating)
- metric for budget breakdown (flights, hotels, food, activities)
- button_group with quick actions (book flight, save itinerary, share)
- rating for user to rate plan satisfaction
- memory_card capturing user's travel preferences (style, budget tier, etc.)

Recommended views:
- "Itinerary" tab: timeline + checklist (packing) + button_group
- "Logistics" tab: table (hotels) + metric (budget) + form (group size)
- "Memory" tab: rating + memory_card
""",

    "code_review": """For pull-request / code-review tasks, consider:
- card for PR summary (title, author, branch, files-changed, +/- LOC, severity)
- diff for the most important code change blocks (before / after with file:line context)
- table for findings (file, line, category, severity, suggestion) — keep ≤ 5 rows
- checklist for review checklist items the user actually needs to verify (tests, security, docs, perf)
- confirmation for the merge / approve gate (this is THE high-stakes decision)
- memory_card capturing the user's review priorities (e.g. "always blocks on missing tests")

Recommended views:
- "Changes" tab: PR summary card + 2-3 diff blocks for the riskiest hunks
- "Findings" tab: findings table + review checklist
- "Decision" tab: confirmation (approve / request-changes) + memory_card

IMPORTANT: every checklist item must be a real verification step the reviewer
performs (e.g. "Tests cover the new error path"), NOT generic chores. Diff
blocks must show the actual code, not pseudo-code or placeholders.
""",
}


def _detect_skill_hint(message: str) -> str | None:
    """Simple keyword-based skill hint detection for demo scenarios."""
    text = message.lower()
    if any(w in text for w in ["contract", "clause", "agreement", "nda", "合同", "条款"]):
        return _DEMO_SKILL_HINTS["contract_review"]
    if any(w in text for w in ["trip", "travel", "itinerary", "vacation", "weekend", "tokyo", "kyoto", "paris", "san francisco", "sf weekend", "napa"]):
        return _DEMO_SKILL_HINTS["trip_planning"]
    if any(w in text for w in ["sales", "customer", "crm", "follow", "pipeline", "briefing", "客户", "跟进"]):
        return _DEMO_SKILL_HINTS["sales_dashboard"]
    if any(w in text for w in ["pull request", "pr ", " pr", "code review", "review this", "merge request", "diff", "refactor", "代码评审", "代码审查"]):
        return _DEMO_SKILL_HINTS["code_review"]
    return None


def _detect_skill_key(message: str) -> str | None:
    """Like _detect_skill_hint but returns the skill identifier (used for sanity-check)."""
    text = message.lower()
    if any(w in text for w in ["contract", "clause", "agreement", "nda", "合同", "条款"]):
        return "contract_review"
    if any(w in text for w in ["trip", "travel", "itinerary", "vacation", "weekend", "tokyo", "kyoto", "paris", "san francisco", "sf weekend", "napa"]):
        return "trip_planning"
    if any(w in text for w in ["sales", "customer", "crm", "follow", "pipeline", "briefing", "客户", "跟进"]):
        return "sales_dashboard"
    if any(w in text for w in ["pull request", "pr ", " pr", "code review", "review this", "merge request", "diff", "refactor", "代码评审", "代码审查"]):
        return "code_review"
    return None


# Off-topic keywords for each skill. If a block's title/content contains any of
# these AND the user's goal does NOT, we drop the block — it's the LLM bleeding
# in examples from other domains (a common failure mode).
_OFF_TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "contract_review": ("sales follow-up", "pipeline", "trip", "itinerary", "napa", "weekend trip", "pull request"),
    "sales_dashboard": ("contract clause", "liability cap", "trip", "itinerary", "napa", "pull request", "code review"),
    "trip_planning": ("contract clause", "liability cap", "sales follow-up", "pipeline", "pull request", "code review"),
    "code_review": (
        "sales follow-up", "pipeline forecast",
        "contract clause", "liability cap",
        "trip", "itinerary", "napa", "weekend trip",
    ),
}


def _filter_off_topic_blocks(
    spec: dict[str, Any], skill_key: str | None, user_goal: str,
) -> dict[str, Any]:
    """Drop blocks whose title/content reference an unrelated demo domain.

    The LLM occasionally pollutes a spec with example blocks from other
    domains (e.g. a "Sales Follow-up" checklist inside a competitive analysis).
    This guard removes such blocks AND prunes the affected views.
    """
    if not skill_key or skill_key not in _OFF_TOPIC_KEYWORDS:
        return spec
    blocked_terms = _OFF_TOPIC_KEYWORDS[skill_key]
    user_lower = user_goal.lower()
    # If the user actually mentioned a "blocked" term themselves, don't filter on it.
    effective_terms = tuple(t for t in blocked_terms if t not in user_lower)
    if not effective_terms:
        return spec

    blocks = spec.get("blocks") or []
    kept_blocks: list[dict[str, Any]] = []
    dropped_ids: set[str] = set()
    for b in blocks:
        if not isinstance(b, dict):
            kept_blocks.append(b)
            continue
        # Build a haystack from the block's textual surface
        title = str(b.get("title") or "").lower()
        props = b.get("props") or {}
        content_parts: list[str] = [title]
        if isinstance(props, dict):
            for v in props.values():
                if isinstance(v, str):
                    content_parts.append(v.lower())
        haystack = " ".join(content_parts)
        if any(term in haystack for term in effective_terms):
            dropped_ids.add(str(b.get("id") or ""))
            continue
        kept_blocks.append(b)

    if not dropped_ids:
        return spec

    spec["blocks"] = kept_blocks
    # Prune dropped block_ids from any view, and remove views that emptied out
    pruned_views: list[dict[str, Any]] = []
    for v in spec.get("views") or []:
        if not isinstance(v, dict):
            pruned_views.append(v)
            continue
        ids = [bid for bid in (v.get("block_ids") or []) if bid not in dropped_ids]
        if ids:
            v = {**v, "block_ids": ids}
            pruned_views.append(v)
    spec["views"] = pruned_views
    return spec


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
            # If we fed the LLM a document, surface it as a Source block so
            # the user can see what's being analyzed alongside the analysis.
            if contract_text:
                _inject_source_document_block(llm_spec, contract_text)

            # Sanity check: drop blocks that bleed in from unrelated demo domains
            # (e.g. a "Sales Follow-up" block inside a competitive-analysis spec).
            original_block_count = len(llm_spec.get("blocks") or [])
            llm_spec = _filter_off_topic_blocks(
                llm_spec, _detect_skill_key(task.input_message), task.input_message
            )
            kept_block_count = len(llm_spec.get("blocks") or [])
            dropped_ratio = (
                (original_block_count - kept_block_count) / original_block_count
                if original_block_count else 0
            )

            # Hard guard: the LLM was so off-topic we'd embarrass ourselves
            # showing the result. Fall through to the curated deterministic
            # fallback (which always stays on-topic for the detected skill).
            #   • fewer than 3 blocks left → unusable
            #   • > 1/3 of blocks were off-topic → spec is incoherent
            if kept_block_count < 3 or dropped_ratio > 0.34:
                pass  # fall through to deterministic
            else:
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
            contract_text=contract_text,
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
        contract_text: str | None = None,
    ) -> dict[str, Any]:
        """Generate a rich multi-block spec without LLM.

        Produces meaningful output for all three demo scenarios so the
        Canvas demo looks good even when the LLM is unavailable/slow.
        """
        zh = any("\u4e00" <= ch <= "\u9fff" for ch in task.input_message[:200])
        text = task.input_message.lower()

        # Detect scenario
        if any(w in text for w in ["contract", "clause", "agreement", "liability", "solidity", "audit", "vulnerab", "reentran", "合同", "条款", "审计"]):
            spec = _fallback_contract(task, run, memory_refs, zh)
        elif any(w in text for w in ["trip", "travel", "itinerary", "vacation", "weekend", "tokyo", "kyoto", "paris", "san francisco", "sf weekend", "napa", "旅行", "行程"]):
            spec = _fallback_trip(task, run, memory_refs)
        elif any(w in text for w in ["sales", "customer", "follow", "pipeline", "threat", "intel", "briefing", "exposure", "客户", "跟进", "情报"]):
            spec = _fallback_sales(task, run, memory_refs, zh)
        elif any(w in text for w in ["pull request", "pr ", " pr", "code review", "review this", "merge request", "refactor", "代码评审", "代码审查"]):
            spec = _fallback_code_review(task, run, memory_refs, zh)
        else:
            spec = _fallback_generic(task, run, memory_refs, memory_snippets, zh)

        # If a source document was provided, surface it in the spec
        if contract_text:
            _inject_source_document_block(spec, contract_text)
        return spec


def _inject_source_document_block(spec: dict[str, Any], document_text: str) -> None:
    """Prepend a 'Source Document' block + view to the spec in-place.

    Lets the user see the document being analyzed alongside the analysis.
    Truncates long docs to ~3000 chars so the panel stays readable.
    """
    zh = any("\u4e00" <= ch <= "\u9fff" for ch in document_text[:200])
    truncated = document_text.strip()
    if len(truncated) > 3000:
        truncated = truncated[:3000] + ("\n\n... (已截断 / truncated)" if zh else "\n\n... (truncated)")

    source_block = {
        "id": "source_document",
        "type": "markdown",
        "title": "📄 原始合同 / Source Document" if zh else "📄 Source Document",
        "props": {"content": truncated},
    }
    source_view = {
        "id": "source_view",
        "label": "原文" if zh else "Source",
        "block_ids": ["source_document"],
    }

    blocks = spec.get("blocks") or []
    # Avoid duplicate insert if already present (e.g. LLM produced its own)
    if not any(b.get("id") == "source_document" for b in blocks):
        spec["blocks"] = [source_block, *blocks]
    views = spec.get("views") or []
    if not any(v.get("id") == "source_view" for v in views):
        spec["views"] = [source_view, *views]


def _fallback_contract(task: Task, run: Run, memory_refs: list[str], zh: bool) -> dict[str, Any]:
    blocks = [
        {"id": "risk_chart", "type": "chart", "title": "Risk Radar", "props": {
            "chart_type": "radar",
            "axes": [
                {"label": "Liability", "score": 9},
                {"label": "Payment", "score": 7},
                {"label": "Data Privacy", "score": 8},
                {"label": "IP Rights", "score": 6},
                {"label": "Termination", "score": 5},
                {"label": "SLA", "score": 4},
            ],
        }},
        {"id": "risk_summary", "type": "card", "title": "Risk Summary", "props": {
            "title": "4 Critical · 4 Medium Risks",
            "content": "Liability cap (§8.1/8.2) is effectively negated: the carve-outs cover nearly every scenario, resulting in near-unlimited exposure.",
            "severity": "high",
        }},
        {"id": "risk_findings", "type": "table", "title": "Risk Findings", "props": {
            "columns": [
                {"key": "clause", "label": "Clause"},
                {"key": "severity", "label": "Severity"},
                {"key": "issue", "label": "Issue"},
            ],
            "rows": [
                {"clause": "§8.1/8.2", "severity": "🔴 Critical", "issue": "Liability cap negated by indemnity carve-outs"},
                {"clause": "§3.2/3.3", "severity": "🔴 High", "issue": "90% payment deferred 180 days post-delivery"},
                {"clause": "§4.2", "severity": "🟠 Medium", "issue": "Post-project data use for model training"},
                {"clause": "§9.1/9.2", "severity": "🟠 Medium", "issue": "Asymmetric termination: 3d vs 90d notice"},
            ],
        }},
        {"id": "revision", "type": "diff", "title": "Suggested Revision — §8.1/8.2", "props": {
            "before": "Vendor liability capped at fees paid, EXCEPT for data breach, IP disputes, regulatory penalties, model errors, business loss, indirect loss, and third-party claims.",
            "after": "Vendor aggregate liability capped at fees paid in prior 12 months. Exclusions limited to: willful misconduct, gross negligence, IP infringement, confirmed data breach. Neither party liable for indirect damages.",
            "context": "Liability & Indemnity",
        }},
        {"id": "next_actions", "type": "checklist", "title": "Next Actions", "props": {
            "items": [
                {"text": "Send revision draft to legal", "checked": False},
                {"text": "Schedule call with vendor counsel", "checked": False},
                {"text": "Prepare BATNA position", "checked": True},
                {"text": "Review insurance coverage gaps", "checked": False},
            ],
        }},
        {"id": "approve", "type": "confirmation", "title": "Approve Revision", "props": {
            "description": "Apply the conservative liability revision to §8.1/8.2 and queue for vendor review?",
            "risk_level": "high",
        }},
        {"id": "memory", "type": "memory_card", "title": "Memory Candidate", "props": {
            "content": "User prefers conservative but negotiation-friendly contract revisions, especially for liability caps and indemnity carve-outs.",
            "memory_type": "preference",
            "confidence": 0.82,
        }},
    ]
    views = [
        {"id": "risks", "label": "Risks", "block_ids": ["risk_chart", "risk_summary", "risk_findings"]},
        {"id": "revision", "label": "Revision", "block_ids": ["revision", "next_actions", "approve"]},
        {"id": "memory", "label": "Memory", "block_ids": ["memory"]},
    ]
    follow_ups = [
        "Re-prioritize these risks by business impact",
        "Draft a counter-proposal email to the vendor",
        "Compare these terms to industry standards",
        "Save my revision style as a reusable template",
    ]
    return _build_fallback_spec("Contract Review", task, run, memory_refs, blocks, views, follow_ups)


def _fallback_trip(task: Task, run: Run, memory_refs: list[str]) -> dict[str, Any]:
    blocks = [
        {"id": "summary", "type": "card", "title": "Trip Snapshot", "props": {
            "title": "✈ San Francisco · 3 days · late September",
            "content": "Late September is SF's best window — Indian summer, ~70°F afternoons, fog largely gone (Karl finally takes a break). Plan covers iconic sights + a Napa wine day-trip + Mission food crawl. 2 people · ~$1500 each excluding flights.",
            "severity": "low",
        }},
        {"id": "itinerary", "type": "timeline", "title": "Day-by-Day Itinerary", "props": {
            "items": [
                {"time": "Day 1 · Fri", "title": "Arrival & Waterfront",
                 "description": "Land at SFO, BART to Powell St (~30 min). Drop bags, walk Embarcadero → Ferry Building marketplace lunch → cable car to Lombard St → sunset at Coit Tower. Dinner in North Beach (Tony's Pizza or Sotto Mare)."},
                {"time": "Day 2 · Sat", "title": "Golden Gate & Mission",
                 "description": "Morning bike across Golden Gate Bridge to Sausalito, ferry back. Afternoon Mission District: Dolores Park, Clarion Alley murals, Mission burrito at La Taqueria. Evening cocktails at Trick Dog or ABV."},
                {"time": "Day 3 · Sun", "title": "Napa Day-Trip",
                 "description": "Drive ~1.5h to Napa Valley. Tastings at 2 wineries (book ahead — Castello di Amorosa for wow factor + Frog's Leap for chill). Lunch at Oxbow Public Market. Back to SFO for evening flight."},
            ],
        }},
        {"id": "budget", "type": "chart", "title": "Budget Breakdown (per person)", "props": {
            "chart_type": "bar",
            "axes": [
                {"label": "Hotel (2 nights)", "score": 480},
                {"label": "Food", "score": 300},
                {"label": "Napa winery", "score": 250},
                {"label": "Local transit", "score": 80},
                {"label": "Activities", "score": 200},
                {"label": "Buffer", "score": 190},
            ],
        }},
        {"id": "packing", "type": "checklist", "title": "Packing & Pre-trip Checklist", "props": {
            "items": [
                {"text": "Layers — SF mornings can be 55°F, afternoons 72°F", "checked": False},
                {"text": "Light windbreaker for Golden Gate Bridge crossing", "checked": False},
                {"text": "Comfortable walking shoes (SF hills are no joke)", "checked": True},
                {"text": "Book Napa winery tastings 1-2 weeks ahead", "detail": "most require reservations now", "checked": False},
                {"text": "Reserve Alcatraz tickets if interested", "detail": "sell out 2-3 weeks out", "checked": False},
                {"text": "Download Clipper card app or buy at BART", "checked": False},
                {"text": "Rental car for Napa only (skip in city)", "checked": False},
            ],
        }},
        {"id": "hotels", "type": "table", "title": "Hotel Shortlist", "props": {
            "columns": [
                {"key": "name", "label": "Hotel"},
                {"key": "area", "label": "Area"},
                {"key": "price", "label": "Per Night"},
                {"key": "rating", "label": "Rating"},
            ],
            "rows": [
                {"name": "Hotel Zephyr", "area": "Fisherman's Wharf", "price": "$240", "rating": "4.3"},
                {"name": "Hotel Zoe", "area": "Fisherman's Wharf", "price": "$280", "rating": "4.5"},
                {"name": "The Marker", "area": "Union Square", "price": "$220", "rating": "4.4"},
                {"name": "Hotel VIA", "area": "SoMa / Embarcadero", "price": "$260", "rating": "4.5"},
            ],
        }},
        {"id": "actions", "type": "button_group", "title": "Quick Actions", "props": {
            "buttons": [
                {"label": "✈ Search SFO flights", "action_id": "search_flights", "variant": "primary"},
                {"label": "🏨 Book Hotel Zoe", "action_id": "book_hotel"},
                {"label": "🍷 Reserve Napa tastings", "action_id": "book_winery"},
                {"label": "💾 Save itinerary", "action_id": "save"},
                {"label": "📤 Share with travel buddy", "action_id": "share"},
            ],
        }},
        {"id": "rating", "type": "rating", "title": "Rate this plan", "props": {
            "label": "How does this plan look so far?",
            "value": 4,
            "max": 5,
        }},
        {"id": "memory", "type": "memory_card", "title": "Memory Candidate", "props": {
            "content": "User likes mixing iconic landmarks with local food & day-trips on weekend getaways. Mid-tier hotels ($220-280/night), ~$1500/person budget excluding flights.",
            "memory_type": "preference",
            "confidence": 0.78,
        }},
    ]
    views = [
        {"id": "itinerary", "label": "Itinerary", "block_ids": ["summary", "itinerary", "packing"]},
        {"id": "logistics", "label": "Logistics", "block_ids": ["budget", "hotels", "actions"]},
        {"id": "memory", "label": "Memory", "block_ids": ["rating", "memory"]},
    ]
    follow_ups = [
        "Add Alcatraz Island to Day 1 (book tickets now)",
        "Swap Napa for Half Moon Bay coastal day instead",
        "Bump to a luxury tier — boutique hotel + Michelin dinner",
        "Save this 'iconic + local food + day-trip' style as my default",
    ]
    return _build_fallback_spec("San Francisco · 3-day Weekend", task, run, memory_refs, blocks, views, follow_ups)


def _fallback_sales(task: Task, run: Run, memory_refs: list[str], zh: bool) -> dict[str, Any]:
    blocks = [
        {"id": "metric_hot", "type": "metric", "title": "Hot Accounts", "props": {
            "label": "Hot Accounts", "value": "3", "delta": "+1 this week",
        }},
        {"id": "metric_pipeline", "type": "metric", "title": "Pipeline", "props": {
            "label": "Projected Pipeline", "value": "$84k", "delta": "+12%",
        }},
        {"id": "metric_pending", "type": "metric", "title": "Pending", "props": {
            "label": "Pending Decisions", "value": "2", "delta": "needs review",
        }},
        {"id": "actions", "type": "checklist", "title": "Recommended Actions", "props": {
            "items": [
                {"text": "Follow up with Acme — ask about procurement timeline", "detail": "stale 4 days", "checked": False},
                {"text": "Send Northstar renewal summary before legal review", "detail": "due Friday", "checked": False},
                {"text": "Confirm Finch Labs security review owner", "detail": "blocking deal", "checked": True},
                {"text": "Schedule Q3 expansion call with TopVendor", "detail": "upsell opportunity", "checked": False},
            ],
        }},
        {"id": "draft", "type": "card", "title": "Draft Email · Acme", "props": {
            "title": "Subject: Following up on procurement timeline",
            "content": "Hi Sarah, hope your week is going well. We discussed potentially closing Q3 — wanted to check whether your procurement team has a clearer view on timeline. Happy to jump on a quick call. Best, Tilo Agent.",
        }},
        {"id": "send", "type": "confirmation", "title": "Send draft email", "props": {
            "description": "Send this draft to Sarah at Acme? External actions require explicit approval.",
            "risk_level": "medium",
        }},
        {"id": "memory", "type": "memory_card", "title": "Memory Candidate", "props": {
            "content": "User wants concise weekly briefings: 3 metrics + actionable checklist + ready-to-send drafts. Prefers gated approval before any outbound action.",
            "memory_type": "preference",
            "confidence": 0.84,
        }},
    ]
    views = [
        {"id": "pipeline", "label": "Pipeline", "block_ids": ["metric_hot", "metric_pipeline", "metric_pending"]},
        {"id": "actions", "label": "Actions", "block_ids": ["actions", "draft", "send"]},
        {"id": "memory", "label": "Memory", "block_ids": ["memory"]},
    ]
    follow_ups = [
        "Show forecasted close dates for these accounts",
        "Draft a stronger follow-up for Acme with discount",
        "Compare this week's pipeline to last month",
        "Schedule this briefing as a recurring weekly task",
    ]
    return _build_fallback_spec("Weekly Sales Briefing", task, run, memory_refs, blocks, views, follow_ups)


def _fallback_code_review(task: Task, run: Run, memory_refs: list[str], zh: bool) -> dict[str, Any]:
    """PR review demo. Every block is a real reviewer action — diff to read,
    findings to verify, checklist to tick, and a confirmation gate to merge."""
    blocks = [
        {"id": "pr_summary", "type": "card", "title": "Pull Request #482", "props": {
            "title": "feat(auth): replace JWT middleware with session-based auth",
            "content": (
                "Author: alice@team · Branch: feat/session-auth → main · "
                "5 files changed · +312 / −187 LOC. "
                "Migrates the auth middleware from stateless JWT to server-side sessions "
                "backed by Redis. Touches login, logout, /me, and the WS handshake."
            ),
            "severity": "medium",
        }},
        {"id": "diff_middleware", "type": "diff", "title": "auth/middleware.py · core change", "props": {
            "before": (
                "def authenticate(request):\n"
                "    token = request.headers.get('Authorization', '').removeprefix('Bearer ')\n"
                "    payload = jwt.decode(token, SECRET, algorithms=['HS256'])\n"
                "    return User.get(payload['sub'])"
            ),
            "after": (
                "def authenticate(request):\n"
                "    sid = request.cookies.get('sid')\n"
                "    if not sid:\n"
                "        raise Unauthorized()\n"
                "    session = redis.get(f'sess:{sid}')\n"
                "    if not session:\n"
                "        raise Unauthorized()\n"
                "    return User.get(session['user_id'])"
            ),
            "context": "Switch from stateless JWT decode to Redis session lookup",
        }},
        {"id": "diff_login", "type": "diff", "title": "auth/routes.py · login endpoint", "props": {
            "before": (
                "@router.post('/login')\n"
                "def login(creds):\n"
                "    user = verify(creds)\n"
                "    return {'token': jwt.encode({'sub': user.id}, SECRET)}"
            ),
            "after": (
                "@router.post('/login')\n"
                "def login(creds, response):\n"
                "    user = verify(creds)\n"
                "    sid = secrets.token_urlsafe(32)\n"
                "    redis.setex(f'sess:{sid}', 86400, {'user_id': user.id})\n"
                "    response.set_cookie('sid', sid, httponly=True, secure=True, samesite='lax')\n"
                "    return {'ok': True}"
            ),
            "context": "Issue secure cookie instead of JWT in body",
        }},
        {"id": "findings", "type": "table", "title": "Review Findings", "props": {
            "columns": [
                {"key": "file", "label": "File:Line"},
                {"key": "category", "label": "Category"},
                {"key": "severity", "label": "Severity"},
                {"key": "issue", "label": "Issue"},
            ],
            "rows": [
                {"file": "auth/middleware.py:14", "category": "Security",  "severity": "🟠 Medium",
                 "issue": "No session-rotation on privilege change — fix-session attack risk"},
                {"file": "auth/routes.py:28",     "category": "Security",  "severity": "🟢 Low",
                 "issue": "Cookie missing __Host- prefix; consider for stricter scope"},
                {"file": "tests/test_auth.py",    "category": "Tests",     "severity": "🔴 High",
                 "issue": "No test for expired-session path (only happy-path covered)"},
                {"file": "ws/handshake.py:42",    "category": "Compat",    "severity": "🟠 Medium",
                 "issue": "WS handshake still reads Authorization header — won't see new cookie"},
                {"file": "docs/auth.md",          "category": "Docs",      "severity": "🟢 Low",
                 "issue": "Mentions JWT in 3 places; needs update"},
            ],
        }},
        {"id": "review_checklist", "type": "checklist", "title": "Reviewer Verification", "props": {
            "items": [
                {"text": "Tests cover expired-session and missing-cookie paths",
                 "detail": "currently only happy-path is tested", "checked": False},
                {"text": "Session is rotated after login & on privilege change",
                 "detail": "prevents session-fixation", "checked": False},
                {"text": "WebSocket handshake updated to read cookie",
                 "detail": "see ws/handshake.py:42", "checked": False},
                {"text": "Backward-compat plan documented for rollout",
                 "detail": "old JWT clients will 401 on deploy", "checked": False},
                {"text": "Redis TTL matches previous JWT exp (24h)",
                 "checked": True},
                {"text": "Docs updated — no stale references to JWT",
                 "checked": False},
            ],
        }},
        {"id": "merge_decision", "type": "confirmation", "title": "Merge Decision", "props": {
            "description": (
                "Approve and merge feat/session-auth into main? "
                "This change is irreversible without a revert PR and will log out "
                "all current users on deploy. 2 of 6 verification items still unchecked."
            ),
            "risk_level": "high",
        }},
        {"id": "memory", "type": "memory_card", "title": "Memory Candidate", "props": {
            "content": (
                "Reviewer prefers: blocks merge until tests cover error paths; "
                "always asks about session-rotation and rollout/compat plans on auth changes."
            ),
            "memory_type": "preference",
            "confidence": 0.83,
        }},
    ]
    views = [
        {"id": "changes",  "label": "Changes",  "block_ids": ["pr_summary", "diff_middleware", "diff_login"]},
        {"id": "findings", "label": "Findings", "block_ids": ["findings", "review_checklist"]},
        {"id": "decision", "label": "Decision", "block_ids": ["merge_decision", "memory"]},
    ]
    follow_ups = [
        "Generate the missing tests for expired-session and WS handshake paths",
        "Draft a 'request changes' comment summarizing the 4 blocking items",
        "Compare this PR's session model to the auth0 reference implementation",
        "Save 'block on missing error-path tests' as my default review rule",
    ]
    return _build_fallback_spec("PR #482 · Auth Refactor Review", task, run, memory_refs, blocks, views, follow_ups)


def _fallback_generic(task: Task, run: Run, memory_refs: list[str], memory_snippets: list[str], zh: bool) -> dict[str, Any]:
    memory_note = f"\n\nRecalled memory: {memory_snippets[0]}" if memory_snippets else ""
    blocks = [
        {"id": "summary", "type": "markdown", "title": "Summary", "props": {
            "content": f"{task.input_message}{memory_note}",
        }},
        {"id": "memory", "type": "memory_card", "title": "Memory Candidate", "props": {
            "content": f"User asked: {task.input_message[:100]}",
            "memory_type": "context",
            "confidence": 0.6,
        }},
    ]
    follow_ups = [
        "Expand on this with more detail",
        "Show me a comparison or alternative",
        "Save this as a reusable template",
    ]
    return _build_fallback_spec("Result", task, run, memory_refs, blocks, [], follow_ups)


def _build_fallback_spec(
    title: str, task: Task, run: Run, memory_refs: list[str],
    blocks: list[dict[str, Any]], views: list[dict[str, Any]],
    follow_ups: list[str] | None = None,
) -> dict[str, Any]:
    spec = ArtifactSpecV1(
        version="tilo/aip/v1",
        artifact_type="document",
        title=title,
        blocks=blocks,
        views=views,
        provenance=[{"type": "task", "id": task.id, "label": task.title}],
        memory_refs=memory_refs,
        run_id=run.id,
        follow_ups=follow_ups or [],
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
        if any(w in text for w in ["pull request", "pr ", "code review", "merge request", "代码评审"]):
            return "code_review"
        return "document"
