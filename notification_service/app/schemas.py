from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TaskEvent(BaseModel):
    event_type: str
    task_id: int
    project_id: int
    actor_id: int | None = None
    timestamp: datetime
    data: dict[str, Any] = Field(default_factory=dict)
