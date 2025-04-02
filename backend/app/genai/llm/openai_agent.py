import os

import instructor
from app.genai.llm.base_agent import Base_LLM_Agent
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

class OpenAIAgent(Base_LLM_Agent):
    def __init__(self):
        super().__init__("OpenAI", "assistant", "user")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.instrcutor_client = instructor.from_openai(self.client)
        self.model = "gpt-4o-mini"
        
    def _generate_normal_response(self, message_history: list[dict]) -> str:
        response = self.client.chat.completions.create(model=self.model, messages=message_history)
        return response.choices[0].message.content
    
    def _generate_structured_response(self, message_history: list[dict], response_model: BaseModel) -> str:
        response = self.instrcutor_client.chat.completions.create(model=self.model, messages=message_history, response_model=response_model)
        return response
    
    def generate_response(self, prompt: str, message_history: list[dict] = [], response_model = str, system_prompt: str = "") -> str:
        return super().generate_response(prompt, message_history, response_model, system_prompt)
    