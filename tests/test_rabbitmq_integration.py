"""
Интеграционные тесты с реальным RabbitMQ.

Запуск в Docker (web видит хост rabbitmq):
  docker compose run --rm web pytest tests/test_rabbitmq_integration.py -m integration -v --no-cov

Локально: поднимите RabbitMQ и укажите RABBITMQ_URL=amqp://guest:guest@localhost:5672/
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import aio_pika
import pytest
from asgiref.sync import sync_to_async
from django.conf import settings

from apps.tasks.models import Task
from apps.users.models import User
from conftest import ProjectFactory, TaskFactory, UserFactory


pytestmark = pytest.mark.integration


async def _receive_one_task_event(url: str, exchange_name: str, timeout: float = 25.0) -> dict[str, Any]:
    connection = await aio_pika.connect_robust(url)
    try:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            exchange_name,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        queue = await channel.declare_queue(exclusive=True)
        await queue.bind(exchange, routing_key="task.*")

        async with queue.iterator() as queue_iter:
            message = await asyncio.wait_for(queue_iter.__anext__(), timeout=timeout)
            async with message.process():
                return json.loads(message.body.decode("utf-8"))
    finally:
        await connection.close()


def _run_async(coro):
    return asyncio.run(coro)


@pytest.mark.django_db(transaction=True)
def test_rabbitmq_settings_point_to_broker():
    # Arrange / Act
    url = settings.RABBITMQ_URL
    exchange = settings.RABBITMQ_EXCHANGE

    # Assert
    assert url.startswith("amqp://")
    assert exchange == "task_events"


@pytest.mark.django_db(transaction=True)
def test_signal_task_created_publishes_to_rabbitmq(rabbitmq_available):
    # Arrange
    manager = UserFactory(role=User.Role.MANAGER)
    member = UserFactory(role=User.Role.MEMBER)
    project = ProjectFactory(owner=manager, members=[member])
    url = rabbitmq_available
    ex_name = settings.RABBITMQ_EXCHANGE

    def create_task_sync():
        return Task.objects.create(
            title="Rabbit integration task",
            description="",
            project=project,
            assignee=member,
            status=Task.Status.TODO,
            priority=Task.Priority.MEDIUM,
        )

    async def run():
        connection = await aio_pika.connect_robust(url)
        try:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                ex_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            queue = await channel.declare_queue(exclusive=True)
            await queue.bind(exchange, routing_key="task.*")

            async with queue.iterator() as queue_iter:
                create_future = asyncio.create_task(sync_to_async(create_task_sync)())
                message = await asyncio.wait_for(queue_iter.__anext__(), timeout=25.0)
                await create_future
                async with message.process():
                    return json.loads(message.body.decode("utf-8"))
        finally:
            await connection.close()

    # Act
    body = asyncio.run(run())

    # Assert
    assert body["event_type"] == "task.created"
    assert body["project_id"] == project.id
    assert body["data"]["title"] == "Rabbit integration task"


@pytest.mark.django_db(transaction=True)
def test_signal_task_updated_publishes_to_rabbitmq(rabbitmq_available):
    # Arrange
    manager = UserFactory(role=User.Role.MANAGER)
    member = UserFactory(role=User.Role.MEMBER)
    project = ProjectFactory(owner=manager, members=[member])
    task = TaskFactory(project=project, assignee=member, title="Before update")

    url = rabbitmq_available
    ex_name = settings.RABBITMQ_EXCHANGE

    async def drain_pending():
        connection = await aio_pika.connect_robust(url)
        try:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                ex_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            queue = await channel.declare_queue(exclusive=True)
            await queue.bind(exchange, routing_key="task.*")
            for _ in range(100):
                try:
                    msg = await asyncio.wait_for(queue.get(fail=False), timeout=0.3)
                except asyncio.TimeoutError:
                    break
                if msg is None:
                    break
                async with msg.process():
                    pass
        finally:
            await connection.close()

    asyncio.run(drain_pending())

    def update_sync():
        task.title = "After update"
        task.save()

    async def run():
        connection = await aio_pika.connect_robust(url)
        try:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                ex_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            queue = await channel.declare_queue(exclusive=True)
            await queue.bind(exchange, routing_key="task.*")

            async with queue.iterator() as queue_iter:
                update_future = asyncio.create_task(sync_to_async(update_sync)())
                message = await asyncio.wait_for(queue_iter.__anext__(), timeout=25.0)
                await update_future
                async with message.process():
                    return json.loads(message.body.decode("utf-8"))
        finally:
            await connection.close()

    # Act
    body = asyncio.run(run())

    # Assert
    assert body["event_type"] == "task.updated"
    assert body["task_id"] == task.id
    assert body["data"]["title"] == "After update"


@pytest.mark.django_db(transaction=True)
def test_published_event_matches_notification_consumer_payload_shape(rabbitmq_available):
    # Arrange (имитация того, что делает consumer: JSON -> поля события)
    manager = UserFactory(role=User.Role.MANAGER)
    member = UserFactory(role=User.Role.MEMBER)
    project = ProjectFactory(owner=manager, members=[member])
    url = rabbitmq_available
    ex_name = settings.RABBITMQ_EXCHANGE

    def create_task_sync():
        return Task.objects.create(
            title="Shape check",
            description="",
            project=project,
            assignee=member,
            status=Task.Status.TODO,
            priority=Task.Priority.LOW,
        )

    async def run():
        connection = await aio_pika.connect_robust(url)
        try:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                ex_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            queue = await channel.declare_queue(exclusive=True)
            await queue.bind(exchange, routing_key="task.*")

            async with queue.iterator() as queue_iter:
                create_future = asyncio.create_task(sync_to_async(create_task_sync)())
                message = await asyncio.wait_for(queue_iter.__anext__(), timeout=25.0)
                await create_future
                async with message.process():
                    return json.loads(message.body.decode("utf-8"))
        finally:
            await connection.close()

    # Act
    body = asyncio.run(run())

    # Assert — те же ключи, что ожидает notification_service TaskEvent
    assert set(body.keys()) >= {"event_type", "task_id", "project_id", "timestamp", "data"}
    assert isinstance(body["data"], dict)
