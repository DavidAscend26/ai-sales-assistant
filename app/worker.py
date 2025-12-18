import asyncio
import os
import structlog
from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.queue.redis_stream import RedisStreamQueue
from app.services.conversation_service import ConversationService
from app.services.twilio_sender import TwilioSender

log = structlog.get_logger()

async def worker_loop(consumer: str):
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=False)
    queue = RedisStreamQueue(redis)
    await queue.ensure_group()

    svc = ConversationService(redis)
    sender = TwilioSender()

    while True:
        resp = await queue.consume(consumer=consumer, count=5, block_ms=5000)
        if not resp:
            continue

        for _, messages in resp:
            for message_id, fields in messages:
                try:
                    user_id = fields[b"user_id"].decode("utf-8")
                    from_number = fields[b"from_number"].decode("utf-8")
                    body = fields[b"body"].decode("utf-8")

                    async with SessionLocal() as db:
                        reply = await svc.handle_message(
                            session=db, user_id=user_id, from_number=from_number, body=body
                        )

                    await sender.send_whatsapp(to_number=from_number, body=reply)

                    await queue.ack(message_id.decode("utf-8") if isinstance(message_id, bytes) else message_id)
                    log.info("message_processed", message_id=message_id, user_id=user_id)

                except Exception as e:
                    log.error("message_failed", message_id=message_id, error=str(e))
                    # No ack → queda pendiente (prod: retry/backoff + DLQ)

async def main():
    configure_logging(settings.LOG_LEVEL)
    consumer = os.environ.get("WORKER_NAME", "worker-1")
    await worker_loop(consumer)

if __name__ == "__main__":
    asyncio.run(main())