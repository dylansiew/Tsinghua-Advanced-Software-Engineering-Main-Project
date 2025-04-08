import json
import os

from app.genai.llm import llm_agent
from app.genai.stt import stt_agent
from app.genai.tts import tts_agent
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
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
    data = tts_agent.convert_text_to_speech(text, output_file)
    json_file = "data/tts/output/test.json"
    with open(json_file, "w") as f:
        json.dump(data.model_dump(), f)
    return data

@test_router.get("/test-audio-stream")
def stream_test_audio():
    test_mp3_path = "data/tts/output/test.mp3"  # Ensure this file exists

    def file_iterator(file_path, chunk_size=1024):
        with open(file_path, mode="rb") as f:
            while chunk := f.read(chunk_size):
                yield chunk

    if not os.path.exists(test_mp3_path):
        return {"error": "Test audio file not found."}

    return StreamingResponse(file_iterator(test_mp3_path), media_type="audio/mpeg")

@test_router.get("/speak")
async def test_speak(text: str):
    print(text)
    return tts_agent._tts(text, "data/tts/output/test.mp3", "voice1")