import json
from typing import Any
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

User = get_user_model()


class TaskConsumer(AsyncWebsocketConsumer):
    """
    Read-only websocket consumer for project task updates.
    """

    project_id: str
    group_name: str

    async def connect(self) -> None:
        self.project_id = self.scope["url_route"]["kwargs"]["project_id"]
        self.group_name = f"project_{self.project_id}"

        query = parse_qs(self.scope.get("query_string", b"").decode())
        token = (query.get("token") or [None])[0]
        if not token:
            await self.close(code=4401)
            return

        user = await self._get_user_from_jwt(token)
        if not user:
            await self.close(code=4401)
            return

        self.user = user
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code: int) -> None:
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(
        self, text_data: str | None = None, bytes_data: bytes | None = None
    ) -> None:
        # Client messages are not accepted in this read-only channel.
        return

    async def send_task_update(self, event: dict[str, Any]) -> None:
        await self.send(
            text_data=json.dumps(
                {
                    "event_type": event.get("event_type"),
                    "task_id": event.get("task_id"),
                    "project_id": event.get("project_id"),
                    "payload": event.get("payload", {}),
                }
            )
        )

    async def _get_user_from_jwt(self, token: str) -> Any | None:
        try:
            validated = AccessToken(str(token))  # type: ignore[arg-type]
            user_id = validated.get("user_id")
            if not user_id:
                return None
            return await User.objects.filter(id=user_id).afirst()
        except TokenError:
            return None
