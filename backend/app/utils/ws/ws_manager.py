from typing import Dict

from fastapi import WebSocket
from models.conversation.conversation import ConversationMessage


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[WebSocket, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections.keys():
            del self.active_connections[user_id]

    async def send_personal_message(self, message: ConversationMessage, user_id: str):
        json_data = {
            "type": message.type.value,
            "data": message.data.model_dump(),
        }
        await self.active_connections[user_id].send_json(json_data)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)
