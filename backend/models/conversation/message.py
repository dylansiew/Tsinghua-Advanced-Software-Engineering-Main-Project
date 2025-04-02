from datetime import datetime
from typing import Optional

from models.conversation.role import MessageRole
from pydantic import BaseModel


class Message(BaseModel):
    conversation_id: str
    created_at: Optional[datetime]
    message_role: MessageRole
    message_content: str

    def to_gpt_message(self):
        return {"role": self.message_role.value, "content": self.message_content}
