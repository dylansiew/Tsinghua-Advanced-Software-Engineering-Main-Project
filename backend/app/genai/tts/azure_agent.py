import base64
import os
import time
from datetime import datetime, timedelta
from typing import Optional

from app.genai.tts.base_agent import Base_TTS_Agent
from azure.cognitiveservices.speech import (
    PronunciationAssessmentConfig, PronunciationAssessmentGradingSystem,
    PronunciationAssessmentGranularity, PronunciationAssessmentResult,
    SessionEventArgs, SpeechConfig, SpeechRecognitionEventArgs,
    SpeechRecognizer, SpeechSynthesizer)
from azure.cognitiveservices.speech.audio import AudioConfig, AudioOutputConfig
from dotenv import load_dotenv

load_dotenv()

min = 0

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


class Azure_TTS_Agent(Base_TTS_Agent):

    def __init__(self):
        super().__init__("Azure")
        self.default_voice = "zh-CN-YunyiMultilingualNeural"
        self.client = SpeechConfig(subscription=os.getenv("AZURE_SPEECH_KEY"), region=os.getenv("AZURE_SPEECH_REGION"))
        self.client.speech_synthesis_language = "zh-CN"
        self.client.speech_recognition_language = "zh-CN"
        self.client.request_word_level_timestamps()
        self.client.speech_synthesis_voice_name = self.default_voice
    
    
    def tts(self, file_path, toSpeak, voice_id: Optional[str] = None):
        config = self.__init_speech_config(voice_id)
        audioOutputConfig = AudioOutputConfig(filename=file_path)
        synthesizer = SpeechSynthesizer(
            speech_config=config, audio_config=audioOutputConfig
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

    def tts_with_viseme(self, file_path, toSpeak, voice_id: Optional[str] = None):
        viseme, word_boundary = self.tts(file_path=file_path, toSpeak=toSpeak, voice_id=voice_id)
        return [
            Viseme(stopTime=item[0], readyPlayerMeViseme=getAvatarViseme(item[1]))
            for item in viseme
        ], word_boundary

    