from typing import Iterable

import structlog

from app.schemas import TaskEvent

logger = structlog.get_logger(__name__)


async def broadcast_websocket(event: TaskEvent, recipients: Iterable[str]) -> None:
    # Реальная WS реализация зависит от transport слоя (Redis pub/sub, gateway и т.д.).
    logger.info(
        "websocket.broadcast",
        event_type=event.event_type,
        task_id=event.task_id,
        recipients=list(recipients),
    )
