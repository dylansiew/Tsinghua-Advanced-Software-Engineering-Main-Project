from pydantic import BaseModel


class Segment(BaseModel):
    start: int
    end: int
    
class Transcription(BaseModel):
    text: str
    segments: list[Segment]
    
