import time
from datetime import datetime

from app.genai.llm import llm_agent
from app.genai.stt import stt_agent
from app.genai.tts import tts_agent
from fastapi import APIRouter
from models.conversation.message import Message
from models.conversation.role import MessageRole
from models.recommendation import Recommendation

test_router = APIRouter(prefix="/test", tags=["Testing Routes"])


@test_router.get("/")
async def test(name: str):
    return {"message": f"Hello, {name}!"}


@test_router.get("/openai")
async def test_openai(query: str):
    return llm_agent.generate_response(query, response_model=Recommendation)


@test_router.get("/stt")
async def test_stt():
    audio_file = "data/stt/input/test.mp3"
    return stt_agent.transcribe(audio_file)


@test_router.get("/tts")
async def test_tts(text: str):
    output_file = "data/tts/output/test.mp3"
    return tts_agent.convert_text_to_speech(text, output_file)
