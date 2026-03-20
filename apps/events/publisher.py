import json
import logging
from typing import Any

import aio_pika
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings

logger = logging.getLogger(__name__)


class RabbitMQPublisher:
    """
    Simple RabbitMQ topic publisher for task domain events.

    Reuses a single robust connection across calls; reconnects automatically
    if the broker drops the connection (aio_pika RobustConnection handles this).
    """

    def __init__(
        self, url: str | None = None, exchange_name: str | None = None
    ) -> None:
        self.url = url or settings.RABBITMQ_URL
        self.exchange_name = exchange_name or settings.RABBITMQ_EXCHANGE
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    async def _get_exchange(self) -> aio_pika.abc.AbstractExchange:
        if self._connection is None or self._connection.is_closed:
            self._connection = await aio_pika.connect_robust(self.url)
            self._channel = None
            self._exchange = None

        if self._channel is None or self._channel.is_closed:
            self._channel = await self._connection.channel()
            self._exchange = None

        if self._exchange is None:
            self._exchange = await self._channel.declare_exchange(
                self.exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )

        return self._exchange

    async def _publish_event(self, event_type: str, payload: dict[str, Any]) -> None:
        exchange = await self._get_exchange()
        message = aio_pika.Message(
            body=json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            type=event_type,
        )
        await exchange.publish(message, routing_key=event_type)

    def publish_event(self, event_type: str, payload: dict[str, Any]) -> None:
        try:
            async_to_sync(self._publish_event)(event_type, payload)
            project_id = payload.get("project_id")
            if project_id:
                channel_layer = get_channel_layer()
                if channel_layer is None:
                    logger.warning("Channel layer is not configured; skipping WS fanout.")
                    return
                async_to_sync(channel_layer.group_send)(
                    f"project_{project_id}",
                    {
                        "type": "send_task_update",
                        "event_type": event_type,
                        "task_id": payload.get("task_id"),
                        "project_id": project_id,
                        "payload": payload,
                    },
                )
        except Exception:  # pragma: no cover
            logger.exception("Failed to publish event '%s'", event_type)
