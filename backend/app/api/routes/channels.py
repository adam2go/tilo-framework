from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.services.channels.telegram.adapter import TelegramAdapter
from app.services.channels.telegram.webhook import TelegramWebhookService

router = APIRouter(prefix="/api/channels", tags=["channels"])


@router.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    settings = get_settings()
    if settings.telegram_webhook_secret and x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid Telegram webhook secret")
    payload = await request.json()
    event = TelegramAdapter().receive(payload)
    return TelegramWebhookService(db, settings).handle(event)
