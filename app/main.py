from fastapi import FastAPI
from redis.asyncio import Redis
import structlog

from app.core.config import settings
from app.core.logging import configure_logging
from app.api.routes_twilio import router as twilio_router
from app.api.routes_chat import router as chat_router

def create_app() -> FastAPI:
    configure_logging(settings.LOG_LEVEL)
    app = FastAPI(title="Kavak Sales Bot", version="0.1.0")

    @app.on_event("startup")
    async def _startup():
        app.state.redis = Redis.from_url(settings.REDIS_URL, decode_responses=False)
        structlog.get_logger().info("startup", env=settings.ENV)

    @app.on_event("shutdown")
    async def _shutdown():
        redis: Redis = app.state.redis
        await redis.close()

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    app.include_router(twilio_router)
    app.include_router(chat_router)

    return app

app = create_app()