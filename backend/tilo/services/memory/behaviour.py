"""User-action-stream → memory candidate analyzer.

The analyzer reads the recent stream of user actions (rejections,
selections, edits, confirmations) recorded as `UIInteractionEvent`s and
proposes memory candidates that capture *behavioural* signal — what the
user has consistently chosen or refused, regardless of which surface
showed the option.

Three rules in v1:

1. Repeated rejection of the same operation/category combination
   → `preference_negative`.
2. Repeated selection of the same option value (across runs/surfaces)
   → `preference_positive`.
3. An edit on a region bound to an existing memory
   → `memory_update_proposed` (the existing memory should be revisited
   next run).

Rules are deterministic, conservative (only fire on clear repeats),
and always emit candidates — never confirmed memories. Tilo's
"candidate-first" memory contract is preserved.

Block ids are recorded inside `structured_payload` for audit only; they
do NOT participate in the dedup `signature`. The framework cares about
*what the user did*, not *which UI control showed it*.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from tilo.models import Memory, UIInteractionEvent

# Public knobs, conservative.
REJECT_THRESHOLD = 3
SELECT_THRESHOLD = 2
RECENT_EVENT_WINDOW = 50  # how many recent events the analyzer inspects


@dataclass(frozen=True)
class BehaviourCandidate:
    """One proposed memory candidate derived from the user-action stream."""

    memory_type: str  # "preference_negative" | "preference_positive" | "memory_update_proposed"
    content: str
    confidence: float
    salience: float
    reason: str
    structured_payload: dict[str, Any]
    # Dedup key. Composed from action semantics, not UI element ids.
    signature: str


class BehaviourMemoryAnalyzer:
    """Derives memory candidates from a stream of UIInteractionEvents.

    Note: the input is called "UIInteractionEvent" by the persistence
    layer (existing schema) but is treated by this analyzer as a generic
    user-action stream. UI-specific fields (block_id, artifact_id) are
    audit metadata, not classification signal.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def analyse(
        self,
        *,
        workspace_id: str,
        project_id: str | None,
        events: list[UIInteractionEvent],
    ) -> list[BehaviourCandidate]:
        if not events:
            return []

        candidates: list[BehaviourCandidate] = []
        candidates.extend(self._detect_repeated_rejects(events))
        candidates.extend(self._detect_repeated_selects(events))
        candidates.extend(self._detect_memory_edit_proposals(events))

        # De-dup against memories that already proposed the same signature.
        seen = self._known_signatures(workspace_id, project_id)
        deduped: list[BehaviourCandidate] = []
        for candidate in candidates:
            if candidate.signature in seen:
                continue
            seen.add(candidate.signature)
            deduped.append(candidate)
        return deduped

    # ------------------------------------------------------------------ #
    # Rule 1: repeated rejects on the same operation/category             #
    # ------------------------------------------------------------------ #

    def _detect_repeated_rejects(self, events: list[UIInteractionEvent]) -> list[BehaviourCandidate]:
        """Group rejections by the *operation* they refused, not by UI block.

        The grouping key is `(operation, risk_level, category)` extracted from
        the action payload. This way three rejects of the same kind of
        decision — even if they happen on different surfaces — are recognised
        as the same behavioural signal.
        """
        rejects_by_signal: dict[tuple[str, str, str], list[UIInteractionEvent]] = defaultdict(list)
        for event in events:
            if event.event_type != "artifact.action.rejected":
                continue
            signal = self._operation_signal(event)
            if signal is None:
                continue
            rejects_by_signal[signal].append(event)

        out: list[BehaviourCandidate] = []
        for (operation, risk_level, category), hits in rejects_by_signal.items():
            if len(hits) < REJECT_THRESHOLD:
                continue
            event_ids = [e.id for e in hits]
            block_ids = sorted({e.block_id for e in hits if e.block_id})
            phrase = self._humanise_operation(operation, category)
            content = (
                f"User has rejected {phrase} {len(hits)} times. Future runs "
                f"should propose a different option instead of repeating this one."
            )
            out.append(
                BehaviourCandidate(
                    memory_type="preference_negative",
                    content=content,
                    confidence=min(0.6 + 0.05 * (len(hits) - REJECT_THRESHOLD), 0.85),
                    salience=0.6,
                    reason=f"Repeated rejection ({len(hits)}×) of operation {operation!r}.",
                    structured_payload={
                        "rule": "repeated_rejects",
                        "operation": operation,
                        "risk_level": risk_level,
                        "category": category,
                        "reject_count": len(hits),
                        "interaction_event_ids": event_ids,
                        # Audit-only: which UI surfaces were used. Not part of
                        # the dedup signature on purpose.
                        "block_ids_seen": block_ids,
                        "behaviour_signature": f"reject:{operation}:{category}",
                    },
                    signature=f"reject:{operation}:{category}",
                )
            )
        return out

    # ------------------------------------------------------------------ #
    # Rule 2: repeated selection of the same option value                 #
    # ------------------------------------------------------------------ #

    def _detect_repeated_selects(self, events: list[UIInteractionEvent]) -> list[BehaviourCandidate]:
        select_counts: dict[str, list[UIInteractionEvent]] = defaultdict(list)
        for event in events:
            if event.event_type not in {"artifact.option.selected", "artifact.action.approved"}:
                continue
            value = self._option_value(event)
            if not value:
                continue
            select_counts[value].append(event)

        out: list[BehaviourCandidate] = []
        for value, hits in select_counts.items():
            if len(hits) < SELECT_THRESHOLD:
                continue
            event_ids = [e.id for e in hits]
            content = (
                f"User has consistently chosen {value!r} ({len(hits)} times). "
                f"Treat it as a default preference for similar decisions."
            )
            out.append(
                BehaviourCandidate(
                    memory_type="preference_positive",
                    content=content,
                    confidence=min(0.55 + 0.07 * (len(hits) - SELECT_THRESHOLD), 0.85),
                    salience=0.55,
                    reason=f"Repeated selection of {value!r} ({len(hits)}×).",
                    structured_payload={
                        "rule": "repeated_selects",
                        "option_value": value,
                        "select_count": len(hits),
                        "interaction_event_ids": event_ids,
                        "behaviour_signature": f"select:{value}",
                    },
                    signature=f"select:{value}",
                )
            )
        return out

    # ------------------------------------------------------------------ #
    # Rule 3: edit action on a memory-bound region                        #
    # ------------------------------------------------------------------ #

    def _detect_memory_edit_proposals(self, events: list[UIInteractionEvent]) -> list[BehaviourCandidate]:
        out: list[BehaviourCandidate] = []
        seen_memory_ids: set[str] = set()
        for event in events:
            if event.event_type != "artifact.block.edited":
                continue
            payload = event.payload_json or {}
            binding = payload.get("state_binding") or {}
            if binding.get("entity_type") != "memory":
                continue
            memory_id = binding.get("entity_id")
            if not memory_id or memory_id in seen_memory_ids:
                continue
            seen_memory_ids.add(memory_id)
            content = (
                f"User edited the content tied to memory {memory_id!r}. "
                f"Surface this memory for review on the next run."
            )
            out.append(
                BehaviourCandidate(
                    memory_type="memory_update_proposed",
                    content=content,
                    confidence=0.7,
                    salience=0.65,
                    reason=f"Edit action on memory {memory_id!r}.",
                    structured_payload={
                        "rule": "memory_edit_proposed",
                        "memory_id": memory_id,
                        "interaction_event_id": event.id,
                        "behaviour_signature": f"memory_edit:{memory_id}",
                    },
                    signature=f"memory_edit:{memory_id}",
                )
            )
        return out

    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _operation_signal(event: UIInteractionEvent) -> tuple[str, str, str] | None:
        """Extract `(operation, risk_level, category)` from an action event.

        Falls back to `("unspecified", "unspecified", "unspecified")` only if
        nothing useful is present. Returning `None` means the event has no
        identifiable operation at all and should be skipped.
        """
        payload = event.payload_json or {}
        action_payload = payload.get("action_payload") if isinstance(payload, dict) else None
        request_payload = payload.get("request_payload") if isinstance(payload, dict) else None

        operation: str | None = None
        risk_level: str | None = None
        category: str | None = None
        for source in (request_payload, action_payload, payload):
            if not isinstance(source, dict):
                continue
            operation = operation or _str_or_none(source.get("operation"))
            risk_level = risk_level or _str_or_none(source.get("risk_level"))
            category = category or _str_or_none(source.get("category"))

        if operation is None:
            return None
        return (operation, risk_level or "unspecified", category or "unspecified")

    @staticmethod
    def _humanise_operation(operation: str, category: str) -> str:
        if category and category != "unspecified":
            return f"{operation.replace('_', ' ')} suggestions in the {category} category"
        return f"{operation.replace('_', ' ')} suggestions"

    @staticmethod
    def _option_value(event: UIInteractionEvent) -> str | None:
        payload = event.payload_json or {}
        for path in (
            ("request_payload", "value"),
            ("request_payload", "option_id"),
            ("request_payload", "choice"),
            ("action_payload", "value"),
            ("action_payload", "option_id"),
            ("action_payload", "choice"),
            ("payload", "value"),
            ("payload", "option_id"),
        ):
            cur: Any = payload
            for key in path:
                if not isinstance(cur, dict):
                    cur = None
                    break
                cur = cur.get(key)
            if isinstance(cur, str) and cur:
                return cur
        return None

    def _known_signatures(self, workspace_id: str, project_id: str | None) -> set[str]:
        """Existing behaviour-derived memory signatures, for dedup."""
        query = self.db.query(Memory).filter(
            Memory.workspace_id == workspace_id,
            Memory.source_type == "ui_behaviour",
            Memory.status.in_(("candidate", "confirmed")),
        )
        if project_id:
            query = query.filter(Memory.project_id == project_id)
        signatures: set[str] = set()
        for memory in query.all():
            payload = memory.structured_payload or {}
            sig = payload.get("behaviour_signature")
            if isinstance(sig, str):
                signatures.add(sig)
        return signatures


def _str_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


__all__ = [
    "BehaviourCandidate",
    "BehaviourMemoryAnalyzer",
    "REJECT_THRESHOLD",
    "SELECT_THRESHOLD",
    "RECENT_EVENT_WINDOW",
]
