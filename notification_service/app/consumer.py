import asyncio
import json

import aio_pika
import structlog

from app.config import settings
from app.handlers.email import send_email_notifications
from app.handlers.telegram import send_telegram_notifications
from app.handlers.websocket import broadcast_websocket
from app.schemas import TaskEvent

logger = structlog.get_logger(__name__)


class NotificationConsumer:
    def __init__(self) -> None:
        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.abc.AbstractChannel | None = None
        self.queue: aio_pika.abc.AbstractQueue | None = None

    async def start(self) -> None:
        self.connection = await self._connect_with_retry()
        self.channel = await self.connection.channel()

        exchange = await self.channel.declare_exchange(
            settings.rabbitmq_exchange,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        self.queue = await self.channel.declare_queue(
            settings.rabbitmq_queue, durable=True
        )
        await self.queue.bind(exchange, routing_key=settings.rabbitmq_routing_key)
        await self.queue.consume(self._on_message)

        logger.info(
            "consumer.started",
            exchange=settings.rabbitmq_exchange,
            queue=settings.rabbitmq_queue,
            routing_key=settings.rabbitmq_routing_key,
        )

    async def _connect_with_retry(self) -> aio_pika.RobustConnection:
        attempts = 0
        while True:
            attempts += 1
            try:
                return await aio_pika.connect_robust(settings.rabbitmq_url)
            except Exception:
                logger.warning("consumer.connect_retry", attempt=attempts)
                await asyncio.sleep(2)

    async def stop(self) -> None:
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        logger.info("consumer.stopped")

    async def _on_message(self, message: aio_pika.IncomingMessage) -> None:
        async with message.process():
            try:
                payload = json.loads(message.body.decode("utf-8"))
                event = TaskEvent(**payload)
                recipients = self._resolve_recipients(event)
                logger.info(
                    "event.received",
                    event_type=event.event_type,
                    task_id=event.task_id,
                    project_id=event.project_id,
                    recipients=recipients,
                )

                await send_email_notifications(event, recipients)
                await send_telegram_notifications(event, recipients)
                await broadcast_websocket(event, recipients)
            except Exception:
                logger.exception("event.process_failed")

    def _resolve_recipients(self, event: TaskEvent) -> list[str]:
        """
        MVP logic. В production обычно lookup идет в User/Project сервисе.
        """
        recipients: set[str] = set()
        assignee_id = event.data.get("assignee_id") or event.data.get("new_assignee_id")
        if assignee_id:
            recipients.add(f"user{assignee_id}@example.com")
            recipients.add(str(assignee_id))
        recipients.add(f"project-{event.project_id}")
        return list(recipients)
