import json
import logging

import aio_pika
from asgiref.sync import async_to_sync
from django.conf import settings

logger = logging.getLogger(__name__)


class RabbitMQPublisher:
    """
    Simple RabbitMQ topic publisher for task domain events.
    """

    def __init__(self, url: str | None = None, exchange_name: str | None = None) -> None:
        self.url = url or settings.RABBITMQ_URL
        self.exchange_name = exchange_name or settings.RABBITMQ_EXCHANGE

    async def _publish_event(self, event_type: str, payload: dict) -> None:
        connection = await aio_pika.connect_robust(self.url)
        try:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                self.exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            message = aio_pika.Message(
                body=json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                type=event_type,
            )
            await exchange.publish(message, routing_key=event_type)
        finally:
            await connection.close()

    def publish_event(self, event_type: str, payload: dict) -> None:
        try:
            async_to_sync(self._publish_event)(event_type, payload)
        except Exception:  # pragma: no cover
            logger.exception("Failed to publish event '%s'", event_type)
