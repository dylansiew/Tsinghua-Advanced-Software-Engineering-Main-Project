import pyttsx3
from app.genai.tts.base_agent import Base_TTS_Agent


class Pyttsx3_Agent(Base_TTS_Agent):
    def __init__(self):
        super().__init__("Pyttsx3")
        self.client = pyttsx3.init()
        self.default_voice = "default"
        
    def _tts(self, text: str, output_file: str, voice: str) -> bool:
        self.client.save_to_file(text, output_file)
        self.client.runAndWait()
        return True
        