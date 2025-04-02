from app.pipelines.conversation.query import talk_to_llm
from fastapi import APIRouter

conversation_router = APIRouter(prefix="/conversation", tags=["Conversation"])


@conversation_router.get("/conversation")
async def get_conversation(conversation_id: str, query: str):
    print("Called talk_to_llm")
    return await talk_to_llm(conversation_id, query)