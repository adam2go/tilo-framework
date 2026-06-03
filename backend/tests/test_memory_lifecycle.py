from helpers import *  # noqa: F401,F403


def test_context_reflection_orid_tone_candidate_and_memory_suppression() -> None:
    with TestClient(app):
        with SessionLocal() as db:
            conversation = ConversationService(db)
            tone_session = conversation.create_or_get_session(
                app_id="contract-review-agent",
                workspace_id="orid-tone-workspace",
                channel=ConversationChannel.web,
            )
            conversation.append_user_message(tone_session.id, "语气不要太强硬，适合发给客户谈判")
            tone_event = UIInteractionEvent(
                workspace_id="orid-tone-workspace",
                event_type="demo.text_followup",
                payload_json={"content": "语气不要太强硬，适合发给客户谈判"},
            )
            db.add(tone_event)
            db.commit()
            db.refresh(tone_event)
            reflection = ContextReflectionService(db).reflect_and_persist(session_id=tone_session.id, trigger_event_id=tone_event.id)

            skip_session = conversation.create_or_get_session(
                app_id="contract-review-agent",
                workspace_id="orid-skip-workspace",
                channel=ConversationChannel.web,
            )
            skip_event = UIInteractionEvent(
                workspace_id="orid-skip-workspace",
                event_type="demo.skip_memory",
                payload_json={"action": "not_now"},
            )
            db.add(skip_event)
            db.commit()
            db.refresh(skip_event)
            skip_reflection = ContextReflectionService(db).reflect_and_persist(session_id=skip_session.id, trigger_event_id=skip_event.id)
            tone_memory = db.query(Memory).filter(Memory.workspace_id == "orid-tone-workspace", Memory.source_type == "context_reflection").one()
            skip_memory_count = db.query(Memory).filter(Memory.workspace_id == "orid-skip-workspace", Memory.source_type == "context_reflection").count()
            reflection_orid = reflection.orid_json
            skip_actions = skip_reflection.proposed_actions_json
            tone_memory_status = tone_memory.status
            tone_memory_confirmed = tone_memory.is_confirmed
            tone_memory_payload = tone_memory.structured_payload

    assert reflection_orid["objective"]["facts"][0].startswith("UI event recorded:")
    assert any("User message:" in fact for fact in reflection_orid["objective"]["facts"])
    assert "likely" not in " ".join(reflection_orid["objective"]["facts"]).lower()
    assert tone_memory_status == "confirmed"
    assert tone_memory_confirmed is True
    assert tone_memory_payload["orid_evidence"]["reflective"]
    assert skip_actions[0]["action"] == "none"
    assert skip_memory_count == 0
