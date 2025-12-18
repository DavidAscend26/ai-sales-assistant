import structlog
from fastapi import Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.session_store import SessionStore
from app.llm.orchestrator import run_agent

log = structlog.get_logger()

class ConversationService:
    def __init__(self, redis: Redis):
        self.sessions = SessionStore(redis)

    @staticmethod
    def depends(request: Request) -> "ConversationService":
        return ConversationService(request.app.state.redis)

    async def handle_message(self, session: AsyncSession, user_id: str, from_number: str, body: str) -> str:
        history = await self.sessions.get_history(user_id)
        await self.sessions.append_turn(user_id, "user", body)

        reply = await run_agent(session=session, history=history, user_message=body)
        await self.sessions.append_turn(user_id, "assistant", reply)

        log.info("reply_ready", user_id=user_id, chars=len(reply))
        return reply