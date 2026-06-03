from pydantic import BaseModel


class TelegramCallbackRef(BaseModel):
    raw: str
    namespace: str
    action: str
    target_id: str


def parse_telegram_callback_data(value: str | None) -> TelegramCallbackRef | None:
    if not value:
        return None
    parts = value.split(":", 2)
    if len(parts) != 3 or parts[0] != "tilo" or not parts[1] or not parts[2]:
        return None
    return TelegramCallbackRef(raw=value, namespace=parts[0], action=parts[1], target_id=parts[2])

