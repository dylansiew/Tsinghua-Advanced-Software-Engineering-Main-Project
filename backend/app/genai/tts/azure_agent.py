import base64
import os
from datetime import datetime, timedelta
from typing import Optional

from app.genai.tts.base_agent import Base_TTS_Agent
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer
from azure.cognitiveservices.speech.audio import AudioOutputConfig
from dotenv import load_dotenv
from models.conversation.conversation import AudioMessage
from models.tts.viseme import Viseme, WordOffset

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

def mp3_to_base64(file_path: str):

    base64_audio = ""

    try:
        with open(file_path, "rb") as file:
            base64_audio = base64.b64encode(file.read()).decode("utf-8")
    except Exception as e:
        print(e)
        return base64_audio

    return base64_audio

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

    def tts_with_viseme(self, file_path, toSpeak, voice_id: Optional[str] = None):
        
        audioOutputConfig = AudioOutputConfig(filename=file_path)
        synthesizer = SpeechSynthesizer(
            speech_config=self.client, audio_config=audioOutputConfig
        )
        sorted_array = []
        word_boundary = []
        start_time = datetime.now()
        offsetArr = []

        def addViseme(e):
            nonlocal offsetArr
            offsetArr.append([e.audio_offset / 10000, e.viseme_id])

        def endViseme(e):
            nonlocal sorted_array, offsetArr
            sorted_array = sorted(offsetArr, key=lambda x: x[0])

        def addBoundary(e):
            nonlocal word_boundary
            offset = WordOffset(
                offset_duration=e.audio_offset,
                word_length=e.word_length,
                text_offset=e.text_offset,
            )
            word_boundary.append(offset)

        synthesizer.viseme_received.connect(addViseme)
        synthesizer.synthesis_completed.connect(endViseme)
        synthesizer.synthesis_word_boundary.connect(addBoundary)
        synthesizer.speak_text(toSpeak)
        while len(sorted_array) == 0 and (datetime.now() - start_time) < timedelta(
            seconds=10
        ):
            pass
        return sorted_array, word_boundary

    def _tts(self, text: str, output_file: str, voice: str) -> bool:            
        viseme, word_boundary = self.tts_with_viseme(
            file_path=output_file, toSpeak=text, voice_id=voice
        )
        return AudioMessage(
            viseme=[
                Viseme(stopTime=item[0], readyPlayerMeViseme=getAvatarViseme(item[1]))
                for item in viseme
            ],
            word_boundary=word_boundary,
            base64_audio=mp3_to_base64(output_file)
        )
