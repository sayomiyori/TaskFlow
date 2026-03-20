from typing import Iterable

import structlog
from aiogram import Bot

from app.config import settings
from app.schemas import TaskEvent

logger = structlog.get_logger(__name__)


async def send_telegram_notifications(
    event: TaskEvent, recipients: Iterable[str]
) -> None:
    if not settings.telegram_bot_token:
        return

    chat_ids = [r for r in recipients if r and "@" not in r]
    if settings.telegram_default_chat_id:
        chat_ids.append(settings.telegram_default_chat_id)
    if not chat_ids:
        return

    bot = Bot(token=settings.telegram_bot_token)
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
    finally:
        await bot.session.close()
