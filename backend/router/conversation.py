from app.pipelines.conversation.query import talk_to_llm
from app.utils.ws import conversation_ws_manager
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from models.conversation.conversation import ConversationMessage

conversation_router = APIRouter(prefix="/conversation", tags=["Conversation"])


@conversation_router.get("/conversation")
async def get_conversation(conversation_id: str, query: str):
    return await talk_to_llm(conversation_id, query)

@conversation_router.websocket("/ws")
async def audio_ws(websocket: WebSocket, user_id: str):
    await conversation_ws_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()   
            conversation_message = ConversationMessage(**data)
            await talk_to_llm(user_id, conversation_message.data)
    except WebSocketDisconnect:
        conversation_ws_manager.disconnect(user_id)
