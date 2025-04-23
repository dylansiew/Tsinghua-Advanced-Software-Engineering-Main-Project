from enum import Enum, unique
from typing import Dict, List

from models.tts.viseme import Viseme, WordOffset
from pydantic import BaseModel


@unique
class ConversationMessageType(str, Enum):
    QUERY: str = "query"
    AUDIO_RESPONSE: str = "audio_response"


class ConversationMessage(BaseModel):
    type: ConversationMessageType
    data: BaseModel

class QueryMessage(BaseModel):
    query: Dict[str, float]

class AudioMessage(BaseModel):
    base64_audio: str
    viseme: List[Viseme]
    word_boundary: List[WordOffset]