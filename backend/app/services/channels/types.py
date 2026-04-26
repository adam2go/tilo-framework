from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field


ChannelName = Literal["telegram"]


class ChannelCapability(BaseModel):
    supports_text: bool = True
    supports_buttons: bool = False
    supports_cards: bool = False
    supports_embedded_web: bool = False
    supports_file_upload: bool = False
    max_message_length: int | None = None
    surface_level: int = 0


class TiloChannelEvent(BaseModel):
    id: str
    channel: ChannelName
    event_type: str
    external_user_id: str
    external_chat_id: str
    text: str | None = None
    callback_data: dict[str, Any] | None = None
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    raw_payload: dict[str, Any] | None = None


class ChannelButton(BaseModel):
    label: str
    action: str | None = None
    target_id: str | None = None
    url: str | None = None


class ChannelOutput(BaseModel):
    channel: ChannelName
    external_chat_id: str
    text: str
    buttons: list[ChannelButton] = Field(default_factory=list)
    artifact_id: str | None = None


class ChannelRenderResult(BaseModel):
    channel: ChannelName
    method: str
    payload: dict[str, Any]
    fallback_text: str | None = None


class ChannelAdapter(Protocol):
    channel: ChannelName
    capability: ChannelCapability

    def receive(self, payload: dict[str, Any]) -> TiloChannelEvent:
        ...

    def render(self, output: ChannelOutput) -> ChannelRenderResult:
        ...

    def send(self, result: ChannelRenderResult) -> dict[str, Any]:
        ...
