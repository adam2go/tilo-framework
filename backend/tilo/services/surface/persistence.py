"""Persist a `ComposedSurface` as a `SurfaceTurn` row (Phase 2).

The persistence layer is the bridge between the composer (pure compute on
a SurfaceSpec) and the rest of the runtime (DB rows, conversation turns,
SSE events).

Persisting a SurfaceTurn:

1. Inserts a row in `surface_turns`.
2. Rewrites the SurfaceSpec's `surface_id` and `turn_id` to match the row
   id, so renderers always receive identifiers consistent with the DB.
3. Optionally appends a `ConversationTurn(turn_type="mini_surface" | "rich_surface_link")`
   so the conversation timeline reflects the new surface.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from tilo.models import Run, SurfaceTurn, Task
from tilo.schemas.surface import BudgetHint, SurfaceSpecV1
from tilo.services.conversations.constants import ConversationTurnType
from tilo.services.conversations.service import ConversationService
from tilo.services.interaction_policy.schemas import InteractionDecision
from tilo.services.surface.composer import ComposedSurface


class SurfaceTurnService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def persist(
        self,
        *,
        task: Task,
        run: Run,
        composed: ComposedSurface,
        decision: InteractionDecision,
        plan_step: dict[str, Any],
        plan_step_index: int,
        ordinal: int,
        session_id: str | None = None,
        artifact_id: str | None = None,
        write_conversation_turn: bool = True,
    ) -> SurfaceTurn:
        spec = composed.spec
        # Insert first so the row id is available, then re-stamp the spec.
        turn_row = SurfaceTurn(
            run_id=run.id,
            session_id=session_id,
            workspace_id=task.workspace_id,
            project_id=task.project_id,
            ordinal=ordinal,
            intent=spec.intent.value,
            budget_hint=spec.budget_hint.value,
            status="ready",
            policy_decision_json=self._policy_decision_to_json(decision, plan_step_index),
            plan_step_index=plan_step_index,
            plan_step_type=plan_step.get("type"),
            artifact_id=artifact_id,
            composer_mode=composed.composer_mode,
            surface_spec_json={},  # filled below
        )
        self.db.add(turn_row)
        self.db.flush()  # populate turn_row.id

        stamped_spec = spec.model_copy(
            update={"surface_id": turn_row.id, "turn_id": turn_row.id}
        )
        # Re-validate after stamping (cheap and defensive).
        stamped_spec = SurfaceSpecV1.model_validate(stamped_spec.model_dump(by_alias=True))
        turn_row.surface_spec_json = stamped_spec.model_dump(by_alias=True, mode="json")
        self.db.commit()
        self.db.refresh(turn_row)

        if session_id and write_conversation_turn:
            self._append_conversation_turn(
                session_id=session_id,
                spec=stamped_spec,
                run=run,
                task=task,
                turn_row=turn_row,
                decision=decision,
            )

        return turn_row

    def list_for_run(self, run_id: str) -> list[SurfaceTurn]:
        return list(
            self.db.query(SurfaceTurn)
            .filter(SurfaceTurn.run_id == run_id)
            .order_by(SurfaceTurn.ordinal.asc(), SurfaceTurn.created_at.asc())
            .all()
        )

    # ------------------------------------------------------------------ #
    # Internals                                                          #
    # ------------------------------------------------------------------ #

    def _append_conversation_turn(
        self,
        *,
        session_id: str,
        spec: SurfaceSpecV1,
        run: Run,
        task: Task,
        turn_row: SurfaceTurn,
        decision: InteractionDecision,
    ) -> None:
        conversation = ConversationService(self.db)
        if not conversation.get_session(session_id):
            return  # session may have been deleted; do not block the run
        turn_type = (
            ConversationTurnType.rich_surface_link
            if spec.budget_hint == BudgetHint.rich
            else ConversationTurnType.mini_surface
        )
        conversation.append_turn(
            session_id,
            turn_type=turn_type,
            role="assistant",
            content=spec.fallback_text,
            surface_type=f"surface.{spec.intent.value}",
            surface_payload=spec.model_dump(by_alias=True, mode="json"),
            artifact_id=turn_row.artifact_id,
            run_id=run.id,
            task_id=task.id,
            policy_decision=self._policy_decision_to_json(decision, turn_row.plan_step_index or 0),
        )

    @staticmethod
    def _policy_decision_to_json(decision: InteractionDecision, step_index: int) -> dict[str, Any]:
        return {
            "step_index": step_index,
            "decision": decision.decision.value,
            "intent": decision.intent.value if decision.intent else None,
            "surface": decision.surface,
            "reason": decision.reason,
            "rule_id": decision.rule_id,
        }


__all__ = ["SurfaceTurnService"]
