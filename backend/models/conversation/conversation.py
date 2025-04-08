from enum import Enum, unique
from typing import List

from models.tts.viseme import Viseme, WordOffset
from pydantic import BaseModel


@unique
class ConversationMessageType(str, Enum):
    QUERY: str = "query"
    AUDIO_RESPONSE: str = "audio_response"


class ConversationMessage(BaseModel):
    type: ConversationMessageType
    data: BaseModel | str

class AudioResponse(BaseModel):
    base64_audio: str
    viseme: List[Viseme]
    word_boundary: List[WordOffset]