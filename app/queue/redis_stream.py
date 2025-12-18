import json
from dataclasses import dataclass
from redis.asyncio import Redis

STREAM_IN = "whatsapp_in"
GROUP = "workers"

@dataclass(frozen=True)
class QueueMessage:
    user_id: str
    from_number: str
    body: str
    raw: dict

class RedisStreamQueue:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def ensure_group(self) -> None:
        try:
            await self.redis.xgroup_create(STREAM_IN, GROUP, id="0-0", mkstream=True)
        except Exception:
            # group probably exists
            pass

    async def publish(self, msg: QueueMessage) -> str:
        data = {
            "user_id": msg.user_id,
            "from_number": msg.from_number,
            "body": msg.body,
            "raw": json.dumps(msg.raw, ensure_ascii=False),
        }
        return await self.redis.xadd(STREAM_IN, data)

    async def consume(self, consumer: str, count: int = 10, block_ms: int = 5000):
        return await self.redis.xreadgroup(
            groupname=GROUP,
            consumername=consumer,
            streams={STREAM_IN: ">"},
            count=count,
            block=block_ms,
        )

    async def ack(self, message_id: str) -> None:
        await self.redis.xack(STREAM_IN, GROUP, message_id)