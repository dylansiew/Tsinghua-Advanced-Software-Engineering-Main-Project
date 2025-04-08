from typing import List

from pydantic import BaseModel


class Viseme(BaseModel):
    stopTime: float
    readyPlayerMeViseme: str

class WordOffset(BaseModel):
    offset_duration: float
    text_offset: int
    word_length: int
    
class AudioData(BaseModel):
    viseme: List[Viseme]
    word_boundary: List[WordOffset]