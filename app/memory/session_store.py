import json
from typing import Any
from redis.asyncio import Redis
from app.core.config import settings

def _key(user_id: str) -> str:
    return f"conv:{user_id}:history"

class SessionStore:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def append_turn(self, user_id: str, role: str, content: str) -> None:
        item = json.dumps({"role": role, "content": content}, ensure_ascii=False)
        await self.redis.rpush(_key(user_id), item)
        max_items = settings.HISTORY_MAX_TURNS * 2
        await self.redis.ltrim(_key(user_id), -max_items, -1)

    async def get_history(self, user_id: str) -> list[dict[str, Any]]:
        raw = await self.redis.lrange(_key(user_id), 0, -1)
        out: list[dict[str, Any]] = []
        for b in raw:
            try:
                out.append(json.loads(b))
            except Exception:
                continue
        return out