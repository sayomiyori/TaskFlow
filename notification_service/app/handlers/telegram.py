from typing import Iterable

import structlog
from aiogram import Bot

from app.config import settings
from app.schemas import TaskEvent

logger = structlog.get_logger(__name__)

_bot: Bot | None = None


def _get_bot() -> Bot | None:
    """Return a module-level singleton Bot, or None if not configured."""
    global _bot
    if not settings.telegram_bot_token:
        return None
    if _bot is None:
        _bot = Bot(token=settings.telegram_bot_token)
    return _bot


async def send_telegram_notifications(
    event: TaskEvent, recipients: Iterable[str]
) -> None:
    bot = _get_bot()
    if bot is None:
        return

    chat_ids = [r for r in recipients if r and "@" not in r]
    if settings.telegram_default_chat_id:
        chat_ids.append(settings.telegram_default_chat_id)
    if not chat_ids:
        return

    text = (
        f"TaskFlow event: {event.event_type}\n"
        f"Task #{event.task_id} in project #{event.project_id}\n"
        f"Data: {event.data}"
    )
    try:
        for chat_id in set(chat_ids):
            await bot.send_message(chat_id=chat_id, text=text)
    except Exception:
        logger.exception(
            "telegram.send_failed", event_type=event.event_type, recipients=chat_ids
        )
