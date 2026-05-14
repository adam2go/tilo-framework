"""Surface composition.

The composer turns one plan step + policy decision into a fully validated
`SurfaceSpec` (per `tilo.surface.v1`). Two backends are provided:

- `DeterministicSurfaceComposer` — never fails, always available; used as
  the fallback for `LLMSurfaceComposer` and as the default when LLMs are
  disabled.
- `LLMSurfaceComposer` — asks a model to fill block content, validates the
  result, falls back to the deterministic composer on any error.

Phase 2 ADR-7 is enforced here: invalid LLM output never reaches the
runtime; the deterministic composer always produces something safe.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from tilo.models import Memory, Run, Task
from tilo.schemas.surface import (
    SURFACE_SCHEMA_VERSION,
    BudgetHint,
    BlockCompat,
    SurfaceBlock,
    SurfaceBlockType,
    SurfaceIntent,
    SurfaceSpecV1,
)
from tilo.services.interaction_policy.schemas import InteractionDecision

__all__ = [
    "ComposerInput",
    "ComposedSurface",
    "DeterministicSurfaceComposer",
    "SurfaceComposer",
]


# --------------------------------------------------------------------------- #
# Inputs / outputs                                                            #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ComposerInput:
    """Everything a composer needs to produce one focused SurfaceSpec."""

    intent: SurfaceIntent
    decision: InteractionDecision
    plan_step: dict[str, Any]
    plan_step_index: int
    task: Task
    run: Run
    memories: list[Memory] = field(default_factory=list)
    tool_outputs: list[dict[str, Any]] = field(default_factory=list)
    artifact_id: str | None = None
    artifact_summary: dict[str, Any] | None = None


@dataclass
class ComposedSurface:
    spec: SurfaceSpecV1
    composer_mode: str  # deterministic | llm | deterministic_fallback
    fallback_reason: str | None = None


# --------------------------------------------------------------------------- #
# Public protocol                                                             #
# --------------------------------------------------------------------------- #


class SurfaceComposer:
    """Base class. Subclasses implement `compose`."""

    def compose(self, payload: ComposerInput) -> ComposedSurface:  # pragma: no cover
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Deterministic composer (always succeeds, no LLM dependency)                 #
# --------------------------------------------------------------------------- #


class DeterministicSurfaceComposer(SurfaceComposer):
    """Produces a structurally-valid SurfaceSpec for every supported intent.

    The output is intentionally minimal but always renderable. It never
    invents domain content beyond what is already in the plan step, recalled
    memories, or recent tool outputs. When in doubt, the composer prefers
    `present_result + fallback` over silently dropping data.
    """

    def compose(self, payload: ComposerInput) -> ComposedSurface:
        intent = payload.intent
        run_id = payload.run.id
        # Surface IDs and turn IDs are derived from run_id + step index so
        # repeated composition for the same step produces stable identifiers.
        # The persistence layer overrides turn_id with the SurfaceTurn row id
        # before saving; this default is only used when a composer caller
        # wants a SurfaceSpec without persisting it (tests).
        surface_id = f"srf_{run_id}_{payload.plan_step_index}"
        turn_id = f"trn_{run_id}_{payload.plan_step_index}"

        builder = _BUILDERS.get(intent, _build_present_result)
        blocks, fallback_text, budget = builder(payload)

        spec_dict = {
            "schema_version": SURFACE_SCHEMA_VERSION,
            "surface_id": surface_id,
            "turn_id": turn_id,
            "run_id": run_id,
            "intent": intent.value,
            "budget_hint": budget.value,
            "block_compat": BlockCompat.graceful.value,
            "blocks": [block.model_dump(by_alias=True, exclude_none=False) for block in blocks],
            "fallback_text": fallback_text,
            "provenance": [
                {"type": "task", "id": payload.task.id, "label": payload.task.title or "task"},
            ],
            "memory_refs": [m.id for m in payload.memories],
            "metadata": {
                "policy_rule_id": payload.decision.rule_id,
                "policy_reason": payload.decision.reason,
                "plan_step_type": payload.plan_step.get("type"),
            },
        }
        spec = SurfaceSpecV1.model_validate(spec_dict)
        return ComposedSurface(spec=spec, composer_mode="deterministic")


# --------------------------------------------------------------------------- #
# Per-intent builders                                                         #
# --------------------------------------------------------------------------- #


def _build_request_approval(payload: ComposerInput) -> tuple[list[SurfaceBlock], str, BudgetHint]:
    step = payload.plan_step
    risk_level = step.get("risk_level") or "medium"
    category = step.get("category") or "general"
    summary = (
        payload.artifact_summary.get("summary") if payload.artifact_summary else None
    ) or (
        f"A {risk_level}-risk decision is required for the {category} category. "
        f"Approve to continue, or reject to stop here."
    )

    decision_block = _decision_block(
        block_id="blk_decision",
        prompt="How should I proceed?",
        options=[
            {"id": "opt_approve", "label": "Approve", "value": "approve", "action_id": "approve"},
            {"id": "opt_reject", "label": "Reject", "value": "reject", "action_id": "reject"},
        ],
        actions=[
            {
                "id": "approve",
                "label": "Approve",
                "action_type": "approve",
                "confirmation_required": True,
                "payload": {
                    "operation": "approve_plan_step",
                    "step_type": step.get("type"),
                    "risk_level": risk_level,
                    "category": category,
                },
            },
            {
                "id": "reject",
                "label": "Reject",
                "action_type": "reject",
                "confirmation_required": False,
                "payload": {"operation": "reject_plan_step"},
            },
        ],
    )
    blocks = [
        _heading(
            block_id="blk_heading",
            text=f"Approval needed · {category}",
            severity="high" if risk_level == "high" else "medium",
        ),
        _text(block_id="blk_body", content=summary),
        decision_block,
    ]
    fallback = f"{summary}\nReply 'approve' or 'reject'."
    return blocks, fallback, BudgetHint.mini


def _build_collect_input(payload: ComposerInput) -> tuple[list[SurfaceBlock], str, BudgetHint]:
    step = payload.plan_step
    blocks = [
        _heading(
            block_id="blk_heading",
            text=f"Information needed · {step.get('type', 'collect_input')}",
        ),
        _form_block(
            block_id="blk_form",
            fields=[
                {
                    "name": "details",
                    "label": "Details",
                    "kind": "textarea",
                    "required": True,
                    "placeholder": "Add the details the agent should use.",
                }
            ],
            submit_action_id="submit_details",
            actions=[
                {
                    "id": "submit_details",
                    "label": "Continue",
                    "action_type": "continue_task",
                    "confirmation_required": False,
                    "payload": {"operation": "submit_collected_input"},
                }
            ],
        ),
    ]
    fallback = "Reply with the details the agent should use to continue."
    return blocks, fallback, BudgetHint.mini


def _build_present_result(payload: ComposerInput) -> tuple[list[SurfaceBlock], str, BudgetHint]:
    step = payload.plan_step
    summary_data = payload.artifact_summary or {}
    summary_text = str(
        summary_data.get("summary")
        or step.get("description")
        or "Result is ready."
    )
    blocks: list[SurfaceBlock] = [
        _heading(block_id="blk_heading", text=f"Result · {step.get('type', 'result')}"),
        _text(block_id="blk_body", content=summary_text),
    ]
    high = int(summary_data.get("high_count") or 0)
    medium = int(summary_data.get("medium_count") or 0)
    low = int(summary_data.get("low_count") or 0)
    if high or medium or low:
        items = []
        if high:
            items.append({"text": f"{high} high-severity finding(s)", "severity": "high"})
        if medium:
            items.append({"text": f"{medium} medium-severity finding(s)", "severity": "medium"})
        if low:
            items.append({"text": f"{low} low-severity finding(s)", "severity": "low"})
        blocks.append(_list_block(block_id="blk_list", items=items))
    fallback = summary_text
    return blocks, fallback, BudgetHint.mini


def _build_offer_choices(payload: ComposerInput) -> tuple[list[SurfaceBlock], str, BudgetHint]:
    step = payload.plan_step
    options = [
        {"id": "opt_a", "label": "Option A", "value": "a", "action_id": "select_choice"},
        {"id": "opt_b", "label": "Option B", "value": "b", "action_id": "select_choice"},
    ]
    blocks = [
        _heading(block_id="blk_heading", text=f"Pick one · {step.get('type', 'choice')}"),
        _decision_block(
            block_id="blk_decision",
            prompt="Choose one to continue.",
            options=options,
            actions=[
                {
                    "id": "select_choice",
                    "label": "Select",
                    "action_type": "select",
                    "confirmation_required": False,
                    "payload": {"operation": "offer_choices"},
                }
            ],
        ),
    ]
    fallback = "Reply with one of: " + ", ".join(option["value"] for option in options) + "."
    return blocks, fallback, BudgetHint.mini


def _build_confirm_memory(payload: ComposerInput) -> tuple[list[SurfaceBlock], str, BudgetHint]:
    proposed = (
        payload.artifact_summary.get("memory_candidate") if payload.artifact_summary else None
    ) or {}
    content = str(proposed.get("content") or "Remember this preference for future runs.")
    memory_type = str(proposed.get("memory_type") or proposed.get("type") or "preference")
    confidence = float(proposed.get("confidence") or 0.7)

    blocks = [
        _heading(block_id="blk_heading", text="Should I remember this?"),
        _text(block_id="blk_body", content=content),
        _decision_block(
            block_id="blk_decision",
            prompt="This becomes durable memory only if you confirm.",
            options=[
                {"id": "opt_yes", "label": "Yes, remember", "value": "confirm", "action_id": "make_memory"},
                {"id": "opt_no", "label": "No", "value": "reject", "action_id": "drop"},
            ],
            actions=[
                {
                    "id": "make_memory",
                    "label": "Remember",
                    "action_type": "create_memory",
                    "confirmation_required": False,
                    "payload": {
                        "content": content,
                        "type": memory_type,
                        "confidence": confidence,
                    },
                },
                {
                    "id": "drop",
                    "label": "Drop",
                    "action_type": "reject",
                    "confirmation_required": False,
                    "payload": {},
                },
            ],
        ),
    ]
    fallback = f"Memory candidate: {content}\nReply 'yes' to remember or 'no' to drop."
    return blocks, fallback, BudgetHint.mini


def _build_show_progress(payload: ComposerInput) -> tuple[list[SurfaceBlock], str, BudgetHint]:
    step = payload.plan_step
    description = str(step.get("description") or "Working...")
    blocks = [
        _heading(block_id="blk_heading", text=f"Progress · {step.get('type', 'work')}"),
        _block(
            block_id="blk_progress",
            block_type=SurfaceBlockType.progress,
            data={"shape": "status", "status": description},
            fallback_text=description,
        ),
    ]
    return blocks, description, BudgetHint.mini


def _build_escalate_to_rich(payload: ComposerInput) -> tuple[list[SurfaceBlock], str, BudgetHint]:
    title = (
        payload.artifact_summary.get("title") if payload.artifact_summary else None
    ) or payload.task.title or "Full result"
    summary_text = (
        payload.artifact_summary.get("summary") if payload.artifact_summary else None
    ) or "Open the full result for details."
    artifact_id = payload.artifact_id or (
        payload.artifact_summary.get("artifact_id") if payload.artifact_summary else None
    )

    if not artifact_id:
        # Fall back gracefully: no artifact yet, but we still need a valid spec.
        return _build_present_result(payload)

    blocks = [
        _heading(block_id="blk_heading", text=title),
        _text(block_id="blk_body", content=summary_text),
        _block(
            block_id="blk_artifact",
            block_type=SurfaceBlockType.artifact_link,
            data={
                "artifact_id": artifact_id,
                "title": title,
                "summary": summary_text,
                "open_action_id": "open_artifact",
            },
            fallback_text=f"Open the full result: {title}.",
            actions=[
                {
                    "id": "open_artifact",
                    "label": "Open",
                    "action_type": "select",
                    "confirmation_required": False,
                    "payload": {"operation": "open_rich", "artifact_id": artifact_id},
                }
            ],
        ),
    ]
    fallback = f"{title}: {summary_text}"
    return blocks, fallback, BudgetHint.rich


def _build_ask_clarification(payload: ComposerInput) -> tuple[list[SurfaceBlock], str, BudgetHint]:
    step = payload.plan_step
    description = str(step.get("description") or "Could you clarify what you want?")
    blocks = [
        _heading(block_id="blk_heading", text="Could you clarify?"),
        _text(block_id="blk_body", content=description),
    ]
    return blocks, description, BudgetHint.mini


_BUILDERS = {
    SurfaceIntent.request_approval: _build_request_approval,
    SurfaceIntent.collect_input: _build_collect_input,
    SurfaceIntent.present_result: _build_present_result,
    SurfaceIntent.offer_choices: _build_offer_choices,
    SurfaceIntent.confirm_memory: _build_confirm_memory,
    SurfaceIntent.show_progress: _build_show_progress,
    SurfaceIntent.escalate_to_rich: _build_escalate_to_rich,
    SurfaceIntent.ask_clarification: _build_ask_clarification,
}


# --------------------------------------------------------------------------- #
# Block helpers                                                               #
# --------------------------------------------------------------------------- #


def _block(
    *,
    block_id: str,
    block_type: SurfaceBlockType,
    data: dict[str, Any],
    fallback_text: str,
    actions: list[dict[str, Any]] | None = None,
) -> SurfaceBlock:
    return SurfaceBlock.model_validate(
        {
            "id": block_id,
            "type": block_type.value,
            "data": data,
            "fallback_text": fallback_text,
            "actions": actions or [],
        }
    )


def _heading(*, block_id: str, text: str, severity: str | None = None) -> SurfaceBlock:
    data: dict[str, Any] = {"text": text}
    if severity:
        data["severity"] = severity
    return _block(
        block_id=block_id,
        block_type=SurfaceBlockType.heading,
        data=data,
        fallback_text=text,
    )


def _text(*, block_id: str, content: str) -> SurfaceBlock:
    return _block(
        block_id=block_id,
        block_type=SurfaceBlockType.text,
        data={"content": content},
        fallback_text=content,
    )


def _list_block(*, block_id: str, items: list[dict[str, Any]]) -> SurfaceBlock:
    fallback = "; ".join(item["text"] for item in items)
    return _block(
        block_id=block_id,
        block_type=SurfaceBlockType.list,
        data={"ordered": False, "items": items},
        fallback_text=fallback or "(empty list)",
    )


def _decision_block(
    *,
    block_id: str,
    prompt: str,
    options: list[dict[str, str]],
    actions: list[dict[str, Any]],
) -> SurfaceBlock:
    fallback = " / ".join(option["label"] for option in options)
    return _block(
        block_id=block_id,
        block_type=SurfaceBlockType.decision,
        data={
            "prompt": prompt,
            "mode": "single",
            "options": options,
        },
        fallback_text=f"{prompt} Options: {fallback}",
        actions=actions,
    )


def _form_block(
    *,
    block_id: str,
    fields: list[dict[str, Any]],
    submit_action_id: str,
    actions: list[dict[str, Any]],
) -> SurfaceBlock:
    return _block(
        block_id=block_id,
        block_type=SurfaceBlockType.form,
        data={"fields": fields, "submit_action_id": submit_action_id},
        fallback_text="Reply with the requested information.",
        actions=actions,
    )


# --------------------------------------------------------------------------- #
# Public defensive composer (validates, never raises)                         #
# --------------------------------------------------------------------------- #


def safe_compose(payload: ComposerInput, composer: SurfaceComposer) -> ComposedSurface:
    """Run a composer and guarantee the output is a valid SurfaceSpec.

    On any error, falls back to the deterministic composer.
    """
    deterministic = DeterministicSurfaceComposer()
    try:
        return composer.compose(payload)
    except (ValidationError, ValueError, TypeError) as exc:
        # Preserve exception class name for diagnostics, drop the message
        # body (may include sensitive material from upstream LLM output).
        fallback = deterministic.compose(payload)
        return ComposedSurface(
            spec=fallback.spec,
            composer_mode="deterministic_fallback",
            fallback_reason=type(exc).__name__,
        )
