from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services.conversation_service import ConversationService

router = APIRouter()

class ChatIn(BaseModel):
    user_id: str
    message: str

@router.post("/chat")
async def chat(
    payload: ChatIn,
    session: AsyncSession = Depends(get_session),
    svc: ConversationService = Depends(ConversationService.depends),
):
    text = await svc.handle_message(
        session=session, user_id=payload.user_id, from_number=payload.user_id, body=payload.message
    )
    return {"reply": text}