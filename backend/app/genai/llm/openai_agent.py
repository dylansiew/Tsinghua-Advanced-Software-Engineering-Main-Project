import json
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
        self.model = "gpt-4.1"

    def _generate_tool_call_response(
        self, message_history: list[dict], tools: list[dict], system_prompt: str
    ) -> str:
        message_history.insert(0, {"role": "system", "content": system_prompt})
        response = self.client.responses.create(
            model=self.model,
            input=message_history,
            tools=tools,
            tool_choice="required",
        )
        return response

    def _generate_normal_response(self, message_history: list[dict]) -> str:
        response = self.client.chat.completions.create(
            model=self.model, messages=message_history
        )
        return response.choices[0].message.content

    def _generate_structured_response(
        self, message_history: list[dict], response_model: BaseModel
    ) -> str:
        response = self.instrcutor_client.chat.completions.create(
            model=self.model, messages=message_history, response_model=response_model
        )
        return response

    # def generate_response(self, query: str, message_history: list[dict] = [], response_model = str, system_prompt: str = "") -> str:
    #     return super().generate_response(query, message_history, response_model, system_prompt)



