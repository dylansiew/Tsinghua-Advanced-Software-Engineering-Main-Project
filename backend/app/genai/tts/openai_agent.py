import os

from app.genai.tts.base_agent import Base_TTS_Agent
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class OpenAI_Agent(Base_TTS_Agent):
    def __init__(self):
        super().__init__("OpenAI")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.default_voice = "nova"
        self.model = "tts-1"
        self.instruction = """Voice: High-energy, upbeat, and encouraging, projecting enthusiasm and motivation.\n\nPunctuation: Short, punchy sentences with strategic pauses to maintain excitement and clarity.\n\nDelivery: Fast-paced and dynamic, with rising intonation to build momentum and keep engagement high.\n\nPhrasing: Action-oriented and direct, using motivational cues to push participants forward.\n\nTone: Positive, energetic, and empowering, creating an atmosphere of encouragement and achievement."""

    def _tts(self, text: str, output_file: str, voice: str) -> bool:
        try:
            with self.client.audio.speech.with_streaming_response.create(
                model=self.model,
                voice=voice or self.default_voice,
                input=text, 
                instructions=self.instruction
            ) as response:
                response.stream_to_file(output_file)
            return True
        except Exception as e:
            print(f"Error in TTS generation: {str(e)}")
            return False