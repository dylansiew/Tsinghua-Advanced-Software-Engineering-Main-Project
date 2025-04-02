import os

from app.genai.stt.base_agent import Base_STT_Agent
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class WhisperAgent(Base_STT_Agent):
    def __init__(self):
        super().__init__("Whisper")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "whisper-1"
        
    def _transcribe_audio(self, audio_file: str) -> str:
        audio = open(audio_file, "rb")
        result = self.client.audio.transcriptions.create(model=self.model, file=audio)
        return result.text
        
        
        