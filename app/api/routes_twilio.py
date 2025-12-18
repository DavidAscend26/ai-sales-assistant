from fastapi import APIRouter, Request
from fastapi.responses import Response
from redis.asyncio import Redis
import structlog

from app.queue.redis_stream import RedisStreamQueue, QueueMessage

log = structlog.get_logger()
router = APIRouter()

def _twiml_empty() -> str:
    return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'

@router.post("/twilio/whatsapp")
async def twilio_whatsapp_webhook(request: Request):
    form = await request.form()
    from_number = str(form.get("From", ""))
    body = str(form.get("Body", "")).strip()

    # user_id could be phone for demo; in prod use hashed id
    user_id = from_number.lower()

    redis: Redis = request.app.state.redis
    queue = RedisStreamQueue(redis)
    await queue.ensure_group()
    await queue.publish(
        QueueMessage(user_id=user_id, from_number=from_number, body=body, raw=dict(form))
    )

    log.info("webhook_enqueued", from_number=from_number, size=len(body))
    return Response(content=_twiml_empty(), media_type="application/xml", status_code=200)