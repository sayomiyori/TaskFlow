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

    Opens a fresh connection per publish call. This is intentional: Django
    signals run in a synchronous context via async_to_sync, which creates and
    tears down a new event loop on each call. A cached connection would be
    bound to the previous (now-closed) loop and raise RuntimeError on reuse.
    """

    def __init__(
        self, url: str | None = None, exchange_name: str | None = None
    ) -> None:
        self.url = url or settings.RABBITMQ_URL
        self.exchange_name = exchange_name or settings.RABBITMQ_EXCHANGE

    async def _publish_event(self, event_type: str, payload: dict[str, Any]) -> None:
        connection = await aio_pika.connect_robust(self.url)
        try:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                self.exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            message = aio_pika.Message(
                body=json.dumps(payload, ensure_ascii=False, default=str).encode(
                    "utf-8"
                ),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                type=event_type,
            )
            await exchange.publish(message, routing_key=event_type)
        finally:
            await connection.close()

    def publish_event(self, event_type: str, payload: dict[str, Any]) -> None:
        try:
            async_to_sync(self._publish_event)(event_type, payload)
            project_id = payload.get("project_id")
            if project_id:
                channel_layer = get_channel_layer()
                if channel_layer is None:
                    logger.warning(
                        "Channel layer is not configured; skipping WS fanout."
                    )
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
