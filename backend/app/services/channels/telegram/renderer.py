from app.services.channels.types import ChannelButton, ChannelOutput, ChannelRenderResult


def telegram_callback_data(action: str, target_id: str) -> str:
    # Telegram callback_data is limited to 64 bytes. Prefer compact refs.
    return f"tilo:{action}:{target_id[:32]}"


class TelegramRenderer:
    channel = "telegram"

    def render(self, output: ChannelOutput) -> ChannelRenderResult:
        return ChannelRenderResult(channel="telegram", method="sendMessage", payload=self.message_payload(output), fallback_text=output.text)

    def plain_text(self, chat_id: str, text: str) -> ChannelRenderResult:
        return self.render(ChannelOutput(channel="telegram", external_chat_id=chat_id, text=text))

    def approval_buttons(self, chat_id: str, text: str, confirmation_id: str, artifact_url: str | None = None) -> ChannelRenderResult:
        buttons = [
            ChannelButton(label="Approve", action="approve_confirmation", target_id=confirmation_id),
            ChannelButton(label="Reject", action="reject_confirmation", target_id=confirmation_id),
        ]
        if artifact_url:
            buttons.append(ChannelButton(label="Open Artifact", url=artifact_url))
        return self.render(ChannelOutput(channel="telegram", external_chat_id=chat_id, text=text, buttons=buttons))

    def memory_buttons(self, chat_id: str, text: str, memory_id: str, artifact_url: str | None = None) -> ChannelRenderResult:
        buttons = [
            ChannelButton(label="Remember", action="confirm_memory", target_id=memory_id),
            ChannelButton(label="Not now", action="reject_memory", target_id=memory_id),
        ]
        if artifact_url:
            buttons.append(ChannelButton(label="Edit in Console", url=artifact_url))
        return self.render(ChannelOutput(channel="telegram", external_chat_id=chat_id, text=text, buttons=buttons))

    def artifact_link_button(self, chat_id: str, text: str, artifact_id: str, public_app_url: str) -> ChannelRenderResult:
        url = f"{public_app_url.rstrip('/')}/artifacts/{artifact_id}?channel=telegram&chat_id={chat_id}"
        return self.render(
            ChannelOutput(
                channel="telegram",
                external_chat_id=chat_id,
                text=text,
                artifact_id=artifact_id,
                buttons=[ChannelButton(label="Open Artifact Surface", url=url)],
            )
        )

    def message_payload(self, output: ChannelOutput) -> dict:
        payload: dict = {"chat_id": output.external_chat_id, "text": output.text}
        rows = []
        for button in output.buttons:
            if button.url:
                rows.append([{"text": button.label, "url": button.url}])
            elif button.action and button.target_id:
                rows.append([{"text": button.label, "callback_data": telegram_callback_data(button.action, button.target_id)}])
        if rows:
            payload["reply_markup"] = {"inline_keyboard": rows}
        return payload

