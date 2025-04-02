import os
from typing import List

from app.utils.db.base_db import BaseDB
from models.conversation.message import Message
from models.conversation.role import MessageRole


class Message_DB(BaseDB):
    def __init__(self):
        super().__init__(query_dir="messages", table_names=["conversation_messages"])

    # @BaseDB.with_refresh
    def insert_message(self, message: Message) -> bool:
        try:
            insert_query_path = self._format_query_path("insert")

            self.cursor.execute(
                open(insert_query_path, "r").read(),
                (
                    message.conversation_id,
                    message.created_at,
                    message.message_role,
                    message.message_content,
                ),
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting message: {e}")
            return False

    # @BaseDB.with_refresh
    def get_all_messages(self, conversation_id: str) -> List[Message]:
        try:
            get_all_query_path = self._format_query_path("get_all")
            self.cursor.execute(
                open(get_all_query_path, "r").read(), (conversation_id,)
            )
            messages = self.cursor.fetchall()
            return [
                Message(
                    conversation_id=message[0],
                    created_at=message[1],
                    message_role=MessageRole(message[2]),
                    message_content=message[3],
                )
                for message in messages
            ]
        except Exception as e:
            print(f"Error getting all messages: {e}")
            return []
