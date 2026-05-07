from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ContextReflection, ConversationTurn, Memory, UIInteractionEvent
from app.services.context_reflection.schemas import ContextReflectionResult, ORIDDecisionalAction
from app.services.conversations.constants import ConversationTurnType
from app.services.conversations.service import ConversationService
from app.services.memory.writer import MemoryWriter
from app.services.trace.recorder import TraceSanitizer

TONE_MARKERS = (
    "tone",
    "softer",
    "friendlier",
    "customer-friendly",
    "negotiation",
    "语气",
    "柔和",
    "客户",
    "谈判",
    "强硬",
)
APPROVAL_MARKERS = ("approve", "approved", "approval", "批准", "同意")
OPEN_REVIEW_MARKERS = ("open_full_review", "open_artifact", "full_review", "open artifact")
REJECT_MEMORY_MARKERS = ("reject_memory", "skip_memory", "not_now", "not now", "以后再说")
CONFIRM_MEMORY_MARKERS = ("confirm_memory", "remember_preference")


class ContextReflectionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.conversations = ConversationService(db)
        self.sanitizer = TraceSanitizer()

    def reflect(
        self,
        *,
        session_id: str,
        trigger_event_id: str | None = None,
        artifact_id: str | None = None,
    ) -> ContextReflectionResult:
        session = self.conversations.get_session(session_id)
        if not session:
            raise ValueError("Conversation session not found")

        event = self.db.get(UIInteractionEvent, trigger_event_id) if trigger_event_id else None
        turns = list(self.conversations.list_turns(session_id, limit=12))
        signal_text = self._signal_text(turns, event)
        lower_signal = signal_text.lower()

        result = ContextReflectionResult(metadata={"session_id": session_id, "trigger_event_id": trigger_event_id})
        if event:
            result.objective.facts.append(self._sanitize(f"UI event recorded: {event.event_type}."))
            if event.action_id:
                result.objective.facts.append(self._sanitize(f"Action id recorded: {event.action_id}."))
            if event.artifact_id or artifact_id:
                result.objective.facts.append(self._sanitize(f"Artifact referenced: {event.artifact_id or artifact_id}."))
        for turn in turns[-4:]:
            if turn.turn_type == ConversationTurnType.user_message and turn.content:
                result.objective.facts.append(self._sanitize(f'User message: "{turn.content}"'))
            if turn.turn_type == ConversationTurnType.observation:
                observed_type = (turn.observation_payload_json or {}).get("event_type") or turn.content
                if observed_type:
                    result.objective.facts.append(self._sanitize(f"Observation turn recorded: {observed_type}."))

        suppress_memory = self._contains_any(lower_signal, REJECT_MEMORY_MARKERS) or self._contains_any(lower_signal, CONFIRM_MEMORY_MARKERS)
        approval_signal = self._contains_any(lower_signal, APPROVAL_MARKERS)
        tone_signal = self._contains_any(lower_signal, TONE_MARKERS)
        full_review_count = self._count_open_review_events(turns, event)

        if approval_signal:
            result.reflective.signals.append("User accepted a proposed revision or confirmation action.")
            result.interpretive.insights.append("Approval can indicate a preference for the approved revision style, but it should remain a candidate until confirmed.")
        if tone_signal:
            result.reflective.signals.append("User expressed a tone or negotiation-style preference.")
            result.interpretive.insights.append("Tone feedback is likely reusable across similar contract and customer-facing follow-up work.")
        if full_review_count >= 2:
            result.reflective.signals.append("User repeatedly opened the full review or artifact surface.")
            result.interpretive.insights.append("Repeated escalation suggests the user wants detailed evidence available for decisions.")
        if suppress_memory:
            result.reflective.signals.append("User confirmed, rejected, or deferred an explicit memory action.")
            result.interpretive.insights.append("The runtime should not create an immediate duplicate memory proposal for this event.")

        if not suppress_memory and tone_signal:
            result.decisional.append(
                ORIDDecisionalAction(
                    action="propose_memory",
                    memory_type="user_preference",
                    content="User prefers softer, customer-friendly negotiation language for follow-up drafts and contract revisions.",
                    why="Tone feedback was expressed in the conversation.",
                    evidence=result.objective.facts[-4:],
                )
            )
        if not suppress_memory and approval_signal:
            result.decisional.append(
                ORIDDecisionalAction(
                    action="propose_memory",
                    memory_type="user_preference",
                    content="User prefers conservative but negotiation-friendly contract revisions.",
                    why="The user approved a revision-related action.",
                    evidence=result.objective.facts[-4:],
                )
            )
        if not suppress_memory and full_review_count >= 2:
            result.decisional.append(
                ORIDDecisionalAction(
                    action="propose_memory",
                    memory_type="user_preference",
                    content="User prefers detailed evidence in the full review surface when making risk decisions.",
                    why="The user repeatedly opened the full review or artifact surface.",
                    evidence=result.objective.facts[-4:],
                )
            )
        if not result.decisional:
            result.decisional.append(ORIDDecisionalAction(action="none", why="No new candidate memory action was warranted."))
        return result

    def reflect_and_persist(
        self,
        *,
        session_id: str,
        trigger_event_id: str | None = None,
        artifact_id: str | None = None,
    ) -> ContextReflection:
        session = self.conversations.get_session(session_id)
        if not session:
            raise ValueError("Conversation session not found")
        result = self.reflect(session_id=session_id, trigger_event_id=trigger_event_id, artifact_id=artifact_id)
        reflection = ContextReflection(
            session_id=session.id,
            workspace_id=session.workspace_id,
            project_id=session.project_id,
            artifact_id=artifact_id,
            trigger_event_id=trigger_event_id,
            orid_json=result.model_dump(mode="json"),
            proposed_actions_json=[action.model_dump(mode="json") for action in result.decisional],
        )
        self.db.add(reflection)
        self.db.flush()

        for action in result.decisional:
            if action.action != "propose_memory" or not action.content:
                continue
            if self._has_duplicate_memory(session.workspace_id, session.project_id, action.content):
                continue
            memory = Memory(
                workspace_id=session.workspace_id,
                project_id=session.project_id,
                scope_type="project" if session.project_id else "workspace",
                scope_id=session.project_id or session.workspace_id,
                type=action.memory_type or "user_preference",
                content=action.content,
                source_type="context_reflection",
                source_id=reflection.id,
                confidence=0.72,
                salience=0.55,
                status="candidate",
                is_confirmed=False,
                structured_payload={
                    "source": "context_reflection",
                    "session_id": session.id,
                    "why": action.why,
                    "orid_evidence": {
                        "objective": result.objective.facts,
                        "reflective": result.reflective.signals,
                        "interpretive": result.interpretive.insights,
                        "decisional_evidence": action.evidence,
                    },
                },
            )
            self.db.add(memory)
            self.db.flush()
            MemoryWriter(self.db).record_event(
                workspace_id=session.workspace_id,
                project_id=session.project_id,
                memory_id=memory.id,
                run_id=None,
                event_type="candidate_created",
                payload_json={"source": "context_reflection", "content": memory.content, "type": memory.type, "why": action.why},
            )
            self.conversations.append_turn(
                session.id,
                turn_type=ConversationTurnType.memory_candidate,
                role="system",
                content=memory.content,
                artifact_id=artifact_id,
                interaction_id=trigger_event_id,
                memory_id=memory.id,
                observation_payload={"source": "context_reflection", "why": action.why},
            )
        self.db.commit()
        self.db.refresh(reflection)
        return reflection

    def _signal_text(self, turns: list[ConversationTurn], event: UIInteractionEvent | None) -> str:
        parts: list[str] = []
        if event:
            parts.extend([event.event_type, event.action_id or "", str(event.payload_json or {})])
        for turn in turns:
            parts.extend([turn.turn_type, turn.content or "", str(turn.observation_payload_json or {})])
        return " ".join(parts)

    def _count_open_review_events(self, turns: list[ConversationTurn], event: UIInteractionEvent | None) -> int:
        count = 1 if event and self._contains_any(self._signal_text([], event).lower(), OPEN_REVIEW_MARKERS) else 0
        for turn in turns:
            text = f"{turn.content or ''} {turn.observation_payload_json or {}}".lower()
            if self._contains_any(text, OPEN_REVIEW_MARKERS):
                count += 1
        return count

    def _has_duplicate_memory(self, workspace_id: str, project_id: str | None, content: str) -> bool:
        stmt = select(Memory).where(Memory.workspace_id == workspace_id, Memory.content == content, Memory.status.in_(("candidate", "confirmed")))
        if project_id:
            stmt = stmt.where(Memory.project_id == project_id)
        return self.db.scalar(stmt) is not None

    def _sanitize(self, text: str) -> str:
        return str(self.sanitizer.sanitize(text))

    @staticmethod
    def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
        return any(marker in text for marker in markers)
