import os
import time

from app.genai.llm.base_agent import Base_LLM_Agent


class Base_TTS_Agent:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.client = None
        self.default_voice = None
        
    def _tts(self, text: str, output_file: str, voice: str) -> bool:            
        raise NotImplementedError("Subclasses must implement _tts")
    
    def _create_directory(self, file_path: str) -> bool:
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            print(f"Directory {directory} does not exist, creating it")
        os.makedirs(directory, exist_ok=True)
    
    def convert_text_to_speech(self, text: str, output_file: str, voice: str = None) -> bool:
        if voice is None:
            voice = self.default_voice
            
        if self.client is None:
            raise ValueError("Client not initialized")
        
        self._create_directory(output_file)
        
        tts_start_time = time.time()
        success = self._tts(text, output_file, voice)
        tts_end_time = time.time()
        tts_duration = tts_end_time - tts_start_time
        
        print(f"Audio generated in {tts_duration} seconds")
        
        return success
    

