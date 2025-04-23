import os


class Base_STT_Agent:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.client = None

    def _file_exists(self, file_path: str) -> bool:
        return os.path.exists(file_path)
    
    def _transcribe_audio(self, audio_file: str) -> str:
        raise NotImplementedError("Subclasses must implement _transcribe_audio")
    
    def transcribe(self, audio_file: str) -> str:
        if self.client is None:
            raise ValueError("Client not initialized")
        
        if not self._file_exists(audio_file):
            raise FileNotFoundError(f"File {audio_file} not found")
        
        return self._transcribe_audio(audio_file)
        
        
