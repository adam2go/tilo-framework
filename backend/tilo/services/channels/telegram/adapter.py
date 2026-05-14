from typing import Any

from tilo.services.channels.telegram.renderer import TelegramRenderer
from tilo.services.channels.telegram.types import parse_telegram_callback_data
from tilo.services.channels.types import ChannelCapability, ChannelOutput, ChannelRenderResult, TiloChannelEvent


telegram_capability = ChannelCapability(
    supports_text=True,
    supports_buttons=True,
    supports_cards=True,
    supports_embedded_web=True,
    supports_file_upload=True,
    max_message_length=4096,
    surface_level=2,
)


class TelegramAdapter:
    channel = "telegram"
    capability = telegram_capability

    def __init__(self) -> None:
        self.renderer = TelegramRenderer()

    def receive(self, payload: dict[str, Any]) -> TiloChannelEvent:
        return normalize_telegram_update(payload)

    def render(self, output: ChannelOutput) -> ChannelRenderResult:
        return self.renderer.render(output)

    def send(self, result: ChannelRenderResult) -> dict[str, Any]:
        # Phase 1 does not call Telegram Bot API. The route returns this payload
        # so deployments can send it through their own worker without logging secrets.
        return {"status": "prepared", "method": result.method, "payload": result.payload}


def normalize_telegram_update(payload: dict[str, Any]) -> TiloChannelEvent:
    if "callback_query" in payload:
        return _normalize_callback_query(payload)
    return _normalize_message(payload)


def _normalize_message(payload: dict[str, Any]) -> TiloChannelEvent:
    message = payload.get("message") or payload.get("edited_message") or {}
    chat = message.get("chat") or {}
    sender = message.get("from") or {}
    text = message.get("text")
    attachments = []
    for key in ("document", "photo", "video", "audio", "voice"):
        if key in message:
            attachments.append({"type": key, "payload": message[key]})
    event_type = "channel.command.start" if text and text.strip().startswith("/start") else "channel.message.received"
    return TiloChannelEvent(
        id=str(message.get("message_id") or payload.get("update_id") or ""),
        channel="telegram",
        event_type=event_type,
        external_user_id=str(sender.get("id") or ""),
        external_chat_id=str(chat.get("id") or ""),
        text=text,
        attachments=attachments,
        raw_payload=payload,
    )


def _normalize_callback_query(payload: dict[str, Any]) -> TiloChannelEvent:
    query = payload.get("callback_query") or {}
    message = query.get("message") or {}
    chat = message.get("chat") or {}
    sender = query.get("from") or {}
    callback_ref = parse_telegram_callback_data(query.get("data"))
    return TiloChannelEvent(
        id=str(query.get("id") or payload.get("update_id") or ""),
        channel="telegram",
        event_type="channel.callback.clicked",
        external_user_id=str(sender.get("id") or ""),
        external_chat_id=str(chat.get("id") or ""),
        text=message.get("text"),
        callback_data=callback_ref.model_dump() if callback_ref else {"raw": query.get("data")},
        raw_payload=payload,
    )
