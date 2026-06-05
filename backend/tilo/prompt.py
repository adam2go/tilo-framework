"""Tilo AIP Prompt Builder — standalone module.

Provides the prompt engineering layer that turns any LLM into a Tilo AIP
spec generator. Extracted from tilo.services.artifact.aip_generator so
developers can use it with their own LLM clients (OpenAI, Anthropic,
LangChain, etc.) without running the full Tilo server.

Quick usage:
    from tilo.prompt import AIPPromptBuilder

    builder = AIPPromptBuilder(goal="Review this contract for payment risks")
    system = builder.system_prompt()
    user   = builder.user_prompt()

    # Use with any LLM:
    # OpenAI:    messages=[{"role":"system","content":system},{"role":"user","content":user}]
    # Anthropic: system=system, messages=[{"role":"user","content":user}]
    # LangChain: ChatPromptTemplate.from_messages([("system",system),("human",user)])

    # Parse the LLM response:
    spec = builder.parse(llm_json_output)
    # spec is an ArtifactSpecV1 or None (on parse failure)
"""

from __future__ import annotations

import json
import re
from typing import Any


# --------------------------------------------------------------------------- #
# Block type reference (same as in aip_generator.py)                          #
# --------------------------------------------------------------------------- #

_BLOCK_TYPE_REFERENCE = """Block types (use as block "type" value):

Content: markdown {content}, table {columns:[{key,label}], rows:[{...}]}, list {items:[{text,severity?}]}, code {content,language?}

Visualization:
  - metric {label, value, delta?}
  - chart {chart_type:"bar|radar|pie", axes:[{label,score}]}
  - progress {percent}

Structured: card {title?, content, severity?}, diff {before, after, context?}, timeline {items:[{time,title,description}]}

Interaction — PREFER THESE, make the artifact engaging, not just a report:
  - checklist {items:[{text, detail?, checked?:bool}]}   ← user can tick items
  - button_group {buttons:[{label, action_id, variant?:"primary|default"}]}
  - rating {label, value:number, max:number}             ← user rates the result
  - form {fields:[{name, label, kind:"text|number"}]}    ← user fills & submits
  - confirmation {description, risk_level?:"high|medium|low"}  ← human-in-the-loop gate
  - memory_card {content, confidence?:0..1}              ← what agent learned

Custom types are fine — unknown types render as JSON viewer.
"""

_SYSTEM_PROMPT_TEMPLATE = """\
You are the Tilo AIP artifact spec generator. Generate a JSON artifact spec for the user goal.

{block_type_reference}

Output exactly this JSON shape:
{{
  "title": "...",
  "views": [{{ "id": "...", "label": "...", "block_ids": ["..."] }}],
  "blocks": [{{ "id": "...", "type": "...", "title": "...", "props": {{...}} }}],
  "follow_ups": ["...", "..."]
}}

Rules:
1. 2–3 views, 5–7 blocks total. Spread blocks across views.
2. Every view block_id MUST exist in blocks.
3. For chart: use {{chart_type, axes:[{{label,score}}]}} — NOT labels/datasets.
4. At least 2 blocks MUST be interactive (checklist, button_group, rating, form, confirmation, memory_card).
5. Always include a `memory_card` block capturing the user's preference or key takeaway.
6. Keep content concise: table rows ≤ 5, list/checklist items ≤ 6, markdown ≤ 150 words.
7. Generate exactly 4 follow_ups that progressively deepen the conversation.
8. Return ONLY JSON. No markdown fences, no commentary.

CRITICAL — STAY ON-TOPIC:
9. Every block must directly serve the user's stated goal. Do not invent unrelated examples.
10. Block titles must be specific. Generic titles like "Example" or "Demo Block" are forbidden.
"""


# --------------------------------------------------------------------------- #
# Built-in skill hints                                                         #
# --------------------------------------------------------------------------- #

BUILTIN_SKILLS: dict[str, dict[str, str]] = {
    "contract_review": {
        "description": "Contract analysis, risk assessment, and revision suggestions.",
        "hints": """\
For contract review tasks, consider:
- chart(radar) for risk distribution across categories (liability, payment, IP, etc.)
- card for risk summary with severity counts and confidence score
- table for detailed risk findings (clause, severity, issue, suggestion)
- diff for revision suggestions (before/after text)
- markdown for full contract text with clause navigation
- memory_card for user preference (e.g. conservative revision style)

Recommended views:
- "Risks" tab: risk chart + risk summary card + risk findings table
- "Clauses" tab: contract text with highlights
- "Revision" tab: diff blocks for suggested changes
- "Memory" tab: memory candidate card
""",
    },
    "sales_dashboard": {
        "description": "Sales pipeline analysis, account insights, follow-up planning.",
        "hints": """\
For sales follow-up tasks, consider:
- metric blocks for KPIs (hot accounts, projected revenue, pending decisions)
- card for key account insights
- list for recommended follow-up actions
- tool_preview for outbound action previews (email drafts, CRM updates)
- memory_card for user preferences (e.g. always prioritise by deal size)

Recommended views:
- "Pipeline" tab: metric blocks + insight cards
- "Actions" tab: action list + tool preview
""",
    },
    "trip_planning": {
        "description": "Travel itinerary planning, logistics, and packing.",
        "hints": """\
For trip planning tasks, consider:
- card with destination summary (vibe, best season, must-knows)
- timeline for day-by-day itinerary
- checklist for packing list or pre-departure tasks (interactive!)
- table for hotel/restaurant comparison (name, area, price, rating)
- metric for budget breakdown (flights, hotels, food, activities)
- button_group for quick actions (book flight, save itinerary)
- rating for user to rate the plan
- memory_card capturing travel preferences (style, budget tier)

Recommended views:
- "Itinerary" tab: timeline + checklist + button_group
- "Logistics" tab: table + metric + form
- "Memory" tab: rating + memory_card
""",
    },
    "code_review": {
        "description": "Pull request review, code quality analysis, merge decision.",
        "hints": """\
For code review tasks, consider:
- card for PR summary (title, author, branch, severity)
- diff for the most important code change blocks (before/after with file:line context)
- table for findings (file, line, category, severity, suggestion) — ≤ 5 rows
- checklist for review steps the user actually needs to verify
- confirmation for the merge/approve gate (the high-stakes decision)
- memory_card capturing review priorities (e.g. "always blocks on missing tests")

Recommended views:
- "Changes" tab: PR summary card + 2-3 diff blocks
- "Findings" tab: findings table + review checklist
- "Decision" tab: confirmation + memory_card
""",
    },
    "competitive_analysis": {
        "description": "Competitive landscape analysis and strategic recommendations.",
        "hints": """\
For competitive analysis tasks, consider:
- table for side-by-side competitor comparison (positioning, strengths, gaps)
- chart(bar) for competitive scores or market share
- markdown for analysis summary and strategic narrative
- list for recommended next steps with priority
- memory_card capturing user's competitive priorities

Recommended views:
- "Comparison" tab: comparison table + bar chart
- "Strategy" tab: analysis summary + next steps list
""",
    },
    "data_analysis": {
        "description": "Data exploration, chart generation, and insight extraction.",
        "hints": """\
For data analysis tasks, consider:
- metric blocks for key KPIs and summary statistics
- chart(bar or line) for trend visualization
- table for the most important data rows (≤ 5)
- markdown for narrative interpretation of findings
- form for user to filter or adjust parameters
- memory_card for analytical preferences

Recommended views:
- "Overview" tab: metric blocks + chart
- "Detail" tab: table + markdown summary
- "Explore" tab: form (filters) + memory_card
""",
    },
    "incident_response": {
        "description": "SRE incident analysis, timeline reconstruction, and post-mortem.",
        "hints": """\
For incident response / post-mortem tasks, consider:
- card for incident summary (service, severity, duration, impact)
- timeline for chronological event sequence (detection → response → resolution)
- table for contributing factors (component, impact, owner)
- checklist for action items and remediation steps
- metric blocks for KPIs (MTTR, affected users, error rate peak)
- confirmation for sign-off on post-mortem document
- memory_card capturing on-call preferences (e.g. "always page primary first")

Recommended views:
- "Timeline" tab: incident card + chronological timeline
- "Factors" tab: contributing factors table + remediation checklist
- "Metrics" tab: metric blocks + confirmation + memory_card
""",
    },
    "meeting_summary": {
        "description": "Meeting notes, decision capture, and action item tracking.",
        "hints": """\
For meeting summary tasks, consider:
- card for meeting overview (title, date, attendees, duration)
- list for key discussion points
- table for decisions made (decision, owner, rationale)
- checklist for action items with owners and due dates (interactive!)
- markdown for detailed notes or context
- memory_card for recurring meeting preferences

Recommended views:
- "Summary" tab: overview card + discussion points list
- "Actions" tab: decisions table + action item checklist
- "Memory" tab: memory_card
""",
    },
    "bug_report": {
        "description": "Bug analysis, reproduction steps, root cause, and fix verification.",
        "hints": """\
For bug analysis / debugging tasks, consider:
- card for bug summary (title, severity, component, reporter, status)
- timeline for reproduction steps (numbered steps to trigger the bug)
- diff for the code change that caused or fixes the bug
- table for affected versions / environments (version, OS, browser, impact)
- checklist for verification steps after the fix
- confirmation for closing the bug ticket
- memory_card for developer debugging preferences

Recommended views:
- "Bug" tab: summary card + reproduction timeline
- "Fix" tab: diff block + affected versions table
- "Verify" tab: checklist + confirmation + memory_card
""",
    },
    "document_review": {
        "description": "Document review, annotation, revision suggestions, and approval.",
        "hints": """\
For document review tasks (not specifically contracts), consider:
- card for document summary (type, version, author, purpose)
- table for section-by-section feedback (section, finding, severity, suggestion)
- diff for specific revision suggestions (before/after text)
- checklist for review criteria (clarity, completeness, accuracy, style)
- confirmation for document approval
- memory_card for reviewer's style preferences

Recommended views:
- "Overview" tab: document card + feedback table
- "Revisions" tab: diff blocks for key changes
- "Approval" tab: review checklist + confirmation + memory_card
""",
    },
    "research_summary": {
        "description": "Research paper or article analysis, key findings, and citations.",
        "hints": """\
For research summarization tasks, consider:
- card for paper/article overview (title, authors, venue, year, TL;DR)
- list for key findings or contributions
- table for methodology comparison or experiment results
- markdown for detailed explanation of a key concept
- rating for user to score paper relevance or quality
- checklist for follow-up reading items
- memory_card for research interests and preferences

Recommended views:
- "Summary" tab: overview card + key findings list
- "Results" tab: results table + methodology explanation
- "Track" tab: checklist + rating + memory_card
""",
    },
    "onboarding_plan": {
        "description": "Developer or employee onboarding checklist and resource guide.",
        "hints": """\
For onboarding plan tasks, consider:
- card for role/project overview (team, stack, key contacts, timeline)
- checklist for week-by-week tasks (interactive — user ticks as they complete)
- table for key resources (name, type, URL, why it matters)
- timeline for onboarding milestones (day 1, week 1, month 1)
- progress block showing overall onboarding completion
- button_group for quick actions (send intro email, join Slack channels)
- memory_card for onboarding preferences

Recommended views:
- "Week 1" tab: overview card + first-week checklist
- "Resources" tab: resources table + milestone timeline
- "Progress" tab: progress block + button_group + memory_card
""",
    },
}


def detect_skill(goal: str) -> str | None:
    """Auto-detect the most appropriate skill name from the user's goal text."""
    text = goal.lower()
    if any(w in text for w in ["contract", "clause", "agreement", "nda", "合同", "条款"]):
        return "contract_review"
    if any(w in text for w in ["trip", "travel", "itinerary", "vacation", "weekend",
                                 "tokyo", "kyoto", "paris", "san francisco"]):
        return "trip_planning"
    if any(w in text for w in ["sales", "pipeline", "crm", "follow-up", "follow up",
                                "customer", "briefing", "客户", "跟进"]):
        return "sales_dashboard"
    if any(w in text for w in ["pull request", "code review", "merge request",
                                "代码评审", "代码审查"]) or re.search(r"\bpr\b", text):
        return "code_review"
    if any(w in text for w in ["competitor", "competitive", "vs ", "versus", "compare companies"]):
        return "competitive_analysis"
    if any(w in text for w in ["incident", "outage", "post-mortem", "postmortem",
                                "sre", "on-call", "oncall", "downtime"]):
        return "incident_response"
    if any(w in text for w in ["meeting", "standup", "retrospective", "action items",
                                "minutes", "meeting notes"]):
        return "meeting_summary"
    if any(w in text for w in ["bug", "issue", "defect", "error", "exception",
                                "stacktrace", "crash", "regression"]):
        return "bug_report"
    if any(w in text for w in ["onboard", "new hire", "new employee", "new developer",
                                "getting started guide", "first week"]):
        return "onboarding_plan"
    if any(w in text for w in ["research", "paper", "article", "study", "findings",
                                "literature", "summarize this"]):
        return "research_summary"
    if any(w in text for w in ["document review", "review this doc", "review this report",
                                "review this proposal"]):
        return "document_review"
    if any(w in text for w in ["data", "dataset", "analyse", "analyze", "chart", "trend",
                                "statistics", "metrics"]):
        return "data_analysis"
    return None


# --------------------------------------------------------------------------- #
# AIPPromptBuilder                                                             #
# --------------------------------------------------------------------------- #

class AIPPromptBuilder:
    """Builds system + user prompts for LLM-driven Tilo AIP spec generation.

    Works with any LLM — OpenAI, Anthropic, LangChain, or plain HTTP.

    Args:
        goal:      The user's task description (what the artifact should address).
        skill:     Skill name (e.g. "contract_review") or None to auto-detect.
                   Use ``list_skills()`` to see all built-in options.
        document:  Optional document text to include (e.g. contract text, PR diff).
        memories:  Optional list of recalled memory strings to include as context.
        language:  Output language hint (default: auto from goal language).
                   Pass "zh" for Chinese output, "en" to force English.

    Example:
        builder = AIPPromptBuilder(
            goal="Review this SaaS contract for payment and IP risks",
            skill="contract_review",
            document=contract_text,
        )
        system = builder.system_prompt()
        user   = builder.user_prompt()
        # → pass to your LLM
        spec = builder.parse(llm_response_text)
    """

    def __init__(
        self,
        goal: str,
        *,
        skill: str | None = "auto",
        document: str | None = None,
        memories: list[str] | None = None,
        language: str | None = None,
        custom_hints: str | None = None,
    ) -> None:
        self.goal = goal
        self.document = document
        self.memories = memories or []
        self.language = language
        self.custom_hints = custom_hints

        # Resolve skill
        if skill == "auto":
            self._skill_key = detect_skill(goal)
        else:
            self._skill_key = skill

    @classmethod
    def from_skill_file(
        cls,
        goal: str,
        skill_path: str | Any,
        **kwargs: Any,
    ) -> "AIPPromptBuilder":
        """Build from a custom skill YAML file (block_hints + view_hints).

        The YAML format matches ``skills/*/skill.yaml``:

            name: my-skill
            block_hints:
              - type: chart
                variant: radar
                use_when: "Showing risk distribution"
            view_hints: |
              Organize into "Overview" and "Detail" tabs.

        Args:
            goal:       The user's task description.
            skill_path: Path to a skill.yaml file.
            **kwargs:   Forwarded to ``__init__`` (document, memories, language).

        Returns:
            An ``AIPPromptBuilder`` configured with the custom skill's hints.
        """
        import yaml
        from pathlib import Path

        data = yaml.safe_load(Path(skill_path).read_text(encoding="utf-8")) or {}
        hints = _render_skill_yaml_hints(data)
        kwargs.pop("skill", None)  # custom hints override skill detection
        return cls(goal, skill=None, custom_hints=hints, **kwargs)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def system_prompt(self) -> str:
        """Return the system prompt to pass to the LLM."""
        lang_instruction = ""
        if self.language == "zh":
            lang_instruction = "\n7b. OUTPUT IN CHINESE. All block titles, content, and follow_ups must be in Chinese.\n"
        elif self.language == "en":
            lang_instruction = "\n7b. OUTPUT IN ENGLISH ONLY.\n"

        base = _SYSTEM_PROMPT_TEMPLATE.format(
            block_type_reference=_BLOCK_TYPE_REFERENCE
        )
        if lang_instruction:
            base = base.replace("8. Return ONLY JSON.", f"{lang_instruction}8. Return ONLY JSON.")
        return base

    def user_prompt(self) -> str:
        """Return the user prompt to pass to the LLM."""
        parts: list[str] = [
            "User goal (SINGLE topic — every block must serve it):\n"
            f'"""\n{self.goal}\n"""\n'
        ]

        if self.document:
            # Truncate very long documents to avoid context limit issues
            doc = self.document[:8000] + ("…[truncated]" if len(self.document) > 8000 else "")
            parts.append(
                "\nDocument text:\n"
                "---BEGIN---\n"
                f"{doc}\n"
                "---END---\n"
            )

        if self.memories:
            memory_text = "\n".join(f"- {m}" for m in self.memories[:5])
            parts.append(f"\nRecalled user preferences / memories:\n{memory_text}\n")

        skill_hints = self._skill_hints()
        if skill_hints:
            parts.append(
                "\nSkill hints (suggested block types for this domain; "
                "all content must still come from the user goal above):\n"
                f"{skill_hints}\n"
            )

        parts.append(
            "\nGenerate the complete artifact spec JSON now. "
            "Every block title and content must directly address the user goal. "
            "No examples from other domains."
        )
        return "".join(parts)

    def parse(self, text: str) -> dict[str, Any] | None:
        """Parse an LLM response string into a validated AIP spec dict.

        Returns:
            A Tilo AIP v1 spec dict if parsing succeeds, or None on failure.
            On success, you can pass the result directly to
            ``ArtifactSpecV1.model_validate(spec)``.
        """
        cleaned = _extract_json(text)
        if not cleaned:
            return None
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            return None
        return _normalise_spec(data, self.goal)

    def messages_openai(self) -> list[dict[str, str]]:
        """Return a messages list ready for OpenAI ``chat.completions.create()``."""
        return [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user",   "content": self.user_prompt()},
        ]

    def messages_anthropic(self) -> dict[str, Any]:
        """Return kwargs ready for Anthropic ``messages.create()``."""
        return {
            "system": self.system_prompt(),
            "messages": [{"role": "user", "content": self.user_prompt()}],
        }

    def messages_langchain(self):
        """Return a LangChain ``ChatPromptTemplate`` instance."""
        try:
            from langchain_core.prompts import ChatPromptTemplate
        except ImportError:
            raise ImportError("pip install langchain-core to use messages_langchain()")
        return ChatPromptTemplate.from_messages([
            ("system", self.system_prompt()),
            ("human",  self.user_prompt()),
        ])

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _skill_hints(self) -> str | None:
        if self.custom_hints:
            return self.custom_hints
        if self._skill_key and self._skill_key in BUILTIN_SKILLS:
            return BUILTIN_SKILLS[self._skill_key]["hints"]
        return None

    # ------------------------------------------------------------------ #
    # Class methods                                                        #
    # ------------------------------------------------------------------ #

    @classmethod
    def list_skills(cls) -> dict[str, str]:
        """Return {skill_name: description} for all built-in skills."""
        return {k: v["description"] for k, v in BUILTIN_SKILLS.items()}


# --------------------------------------------------------------------------- #
# Custom skill YAML rendering                                                  #
# --------------------------------------------------------------------------- #

def _render_skill_yaml_hints(data: dict[str, Any]) -> str:
    """Turn a skill.yaml dict (block_hints + view_hints) into a prompt string."""
    lines: list[str] = []
    name = data.get("name") or "this domain"
    lines.append(f"For {name} tasks, consider these block types:")

    for hint in data.get("block_hints", []) or []:
        if not isinstance(hint, dict):
            continue
        block_type = hint.get("type", "")
        variant = hint.get("variant")
        use_when = hint.get("use_when", "")
        label = f"{block_type}({variant})" if variant else block_type
        lines.append(f"- {label}: {use_when}")

    view_hints = data.get("view_hints")
    if view_hints:
        lines.append("\nRecommended views:")
        lines.append(str(view_hints).strip())

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Internal parsing helpers                                                     #
# --------------------------------------------------------------------------- #

def _extract_json(text: str) -> str | None:
    """Extract a JSON object from LLM output that may contain prose or fences."""
    # Strip markdown code fences
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    text = text.replace("```", "").strip()

    # Try the whole string first
    if text.startswith("{"):
        return text

    # Find the outermost { ... }
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)

    return None


def _normalise_spec(data: dict[str, Any], goal: str) -> dict[str, Any]:
    """Ensure the parsed dict is a valid AIP v1 spec, filling in required fields."""
    blocks: list[dict[str, Any]] = data.get("blocks") or []
    views: list[dict[str, Any]] = data.get("views") or []

    # Assign missing IDs
    for i, block in enumerate(blocks):
        if not block.get("id"):
            block["id"] = f"b{i}"
        # Normalise props: support both 'props' and 'data'
        if "data" in block and "props" not in block:
            block["props"] = block.pop("data")
        if "props" not in block:
            block["props"] = {}

    # Build a default view if none provided
    if not views and blocks:
        views = [{"id": "main", "label": "Result", "block_ids": [b["id"] for b in blocks]}]

    # Ensure every view only references existing block IDs
    block_ids = {b["id"] for b in blocks}
    for view in views:
        view["block_ids"] = [bid for bid in view.get("block_ids", []) if bid in block_ids]

    return {
        "version": "tilo/aip/v1",
        "title": data.get("title") or _default_title(goal),
        "status": "ready",
        "blocks": blocks,
        "views": views,
        "actions": data.get("actions") or [],
        "follow_ups": data.get("follow_ups") or [],
        "memory_refs": [],
        "provenance": [{"type": "aip_prompt_builder", "id": "tilo.prompt.v1"}],
    }


def _default_title(goal: str) -> str:
    words = goal.split()[:6]
    return " ".join(words) + ("…" if len(goal.split()) > 6 else "")
