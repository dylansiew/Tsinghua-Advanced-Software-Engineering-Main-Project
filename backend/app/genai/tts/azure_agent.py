import base64
import json
import os
import queue
import threading
from datetime import datetime, timedelta
from typing import Optional

from app.genai.tts.base_agent import Base_TTS_Agent
from azure.cognitiveservices.speech import (ResultReason, SpeechConfig,
                                            SpeechSynthesizer)
from azure.cognitiveservices.speech.audio import (
    AudioOutputConfig, AudioOutputStream, PullAudioOutputStream,
    PushAudioOutputStreamCallback)
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
from models.tts.viseme import AudioResponse, Viseme, WordOffset

load_dotenv()


visemeMapping = {
    0: "viseme_sil",
    1: "viseme_aa",
    2: "viseme_aa",
    3: "viseme_O",
    4: "viseme_U",
    5: "viseme_CH",
    6: "viseme_RR",
    7: "viseme_U",
    8: "viseme_O",
    9: "viseme_U",
    10: "viseme_O",
    11: "viseme_aa",
    12: "viseme_CH",
    13: "viseme_RR",
    14: "viseme_nn",
    15: "viseme_SS",
    16: "viseme_CH",
    17: "viseme_TH",
    18: "viseme_FF",
    19: "viseme_TH",
    20: "viseme_kk",
    21: "viseme_PP",
}


def getAvatarViseme(id: int):
    if id < len(visemeMapping) and id >= 0:
        return visemeMapping[id]
    else:
        return "viseme_sil"


class Azure_Agent(Base_TTS_Agent):

    def __init__(self):
        super().__init__("Azure")
        self.default_voice = "zh-CN-YunyiMultilingualNeural"
        self.client = SpeechConfig(
            subscription=os.getenv("AZURE_SPEECH_KEY"),
            region=os.getenv("AZURE_SPEECH_REGION"),
        )
        self.client.speech_synthesis_language = "zh-CN"
        self.client.speech_recognition_language = "zh-CN"
        self.client.request_word_level_timestamps()
        self.client.speech_synthesis_voice_name = self.default_voice
   
    def tts_with_viseme_stream(self, toSpeak, voice_id: Optional[str] = None):
        class StreamCallback(PushAudioOutputStreamCallback):
            def __init__(self, audio_queue):
                super().__init__()
                self.audio_queue = audio_queue

            def write(self, data):
                if data:
                    self.audio_queue.put(data)
                    return len(data)
                return 0

            def close(self):
                self.audio_queue.put(None)
                return super().close()

        audio_queue = queue.Queue()
        stream = PullAudioOutputStream(StreamCallback(audio_queue))
        audioOutputConfig = AudioOutputConfig(stream=stream)
        synthesizer = SpeechSynthesizer(speech_config=self.client, audio_config=audioOutputConfig)

        viseme_events = queue.Queue()
        word_events = queue.Queue()

        def add_viseme(e):
            viseme_events.put({
                "type": "viseme",
                "timestamp": e.audio_offset / 10000,
                "viseme_id": getAvatarViseme(e.viseme_id)
            })

        def add_boundary(e):
            word_events.put({
                "type": "word",
                "timestamp": e.audio_offset / 10000,
                "word_length": e.word_length,
                "text_offset": e.text_offset,
                "text": e.text
            })

        synthesizer.viseme_received.connect(add_viseme)
        synthesizer.synthesis_word_boundary.connect(add_boundary)

        synthesis_done = threading.Event()

        def on_synthesis_completed(e):
            synthesis_done.set()
            audio_queue.put(None)

        synthesizer.synthesis_completed.connect(on_synthesis_completed)

        synthesis_thread = threading.Thread(target=synthesizer.speak_text, args=(toSpeak,))
        synthesis_thread.start()

        while not synthesis_done.is_set() or not audio_queue.empty():
            # Yield all visemes in the queue
            while not viseme_events.empty():
                yield viseme_events.get()

            # Yield all word boundaries
            while not word_events.empty():
                yield word_events.get()

            # Yield audio bytes
            try:
                audio_chunk = audio_queue.get(timeout=0.1)
                if audio_chunk is None:
                    break
                yield {
                    "type": "audio",
                    "data": audio_chunk
                }
            except queue.Empty:
                continue
        
    # def _tts(self, text: str, output_file: str, voice: str) -> bool:
    #     viseme, word_boundary = self.tts_with_viseme(
    #         file_path=output_file, toSpeak=text, voice_id=voice
    #     )
    #     return AudioResponse(
    #         viseme=[
    #             Viseme(stopTime=item[0], readyPlayerMeViseme=getAvatarViseme(item[1]))
    #             for item in viseme
    #         ],
    #         word_boundary=word_boundary,
    #     )

    def _tts(self, text: str, output_file: str, voice: str) -> StreamingResponse:
        def audio_stream():
            for event in self.tts_with_viseme_stream(toSpeak=text, voice_id=voice):
                if event["type"] == "audio":
                    yield event["data"]

        return StreamingResponse(audio_stream(), media_type="audio/wav")
