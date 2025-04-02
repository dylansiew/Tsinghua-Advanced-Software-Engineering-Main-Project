import os

import httpx
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AUDIO_SAVE_PATH = "output.mp3"  # or generate dynamically if needed


class SpeakRequest(BaseModel):
    text: str


async def stream_and_save_tts(text: str, file_path: str):
    url = "https://api.openai.com/v1/audio/speech"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    payload = {
        "model": "tts-1",
        "input": text,
        "voice": "nova",
        "response_format": "mp3",
        "speed": 1.0
    }

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as response:
            with open(file_path, "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)           # Save to file
                    yield chunk              # Yield to client


@app.get("/speak")
async def speak(text: str):
    return StreamingResponse(
        stream_and_save_tts(text, AUDIO_SAVE_PATH),
        media_type="audio/mpeg"
    )
