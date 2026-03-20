from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from app.consumer import NotificationConsumer

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger(__name__)

consumer = NotificationConsumer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await consumer.start()
    logger.info("notification_service.started")
    try:
        yield
    finally:
        await consumer.stop()
        logger.info("notification_service.stopped")


app = FastAPI(title="TaskFlow Notification Service", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
