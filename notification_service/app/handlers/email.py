from email.message import EmailMessage
from typing import Iterable

import aiosmtplib
import structlog

from app.config import settings
from app.schemas import TaskEvent

logger = structlog.get_logger(__name__)


async def send_email_notifications(event: TaskEvent, recipients: Iterable[str]) -> None:
    recipient_list = [r for r in recipients if "@" in r]
    if not recipient_list:
        return

    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = ", ".join(recipient_list)
    message["Subject"] = f"TaskFlow event: {event.event_type}"
    message.set_content(
        f"Event: {event.event_type}\n"
        f"Task ID: {event.task_id}\n"
        f"Project ID: {event.project_id}\n"
        f"Actor ID: {event.actor_id}\n"
        f"Data: {event.data}\n"
    )

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username or None,
            password=settings.smtp_password or None,
        )
    except Exception:
        logger.exception("email.send_failed", event_type=event.event_type, recipients=recipient_list)
