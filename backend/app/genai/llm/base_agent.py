import time

from pydantic import BaseModel


class Base_LLM_Agent:
    def __init__(self, agent_name: str, agent_prefix: str, user_prefix: str):
        self.agent_name = agent_name
        self.agent_prefix = agent_prefix
        self.user_prefix = user_prefix

    def __validate_message_history(self, message_history) -> bool:
        if not isinstance(message_history, list):
            return False
        if not all(isinstance(message, dict) for message in message_history):
            return False
        if not all(
            key in message for message in message_history for key in ["role", "content"]
        ):
            return False

        # Validate prefix alternation
        expected_prefixes = []
        if len(message_history) > 0:
            expected_prefixes = [
                self.user_prefix if i % 2 == 0 else self.agent_prefix
                for i in range(len(message_history))
            ]
            actual_prefixes = [msg["role"] for msg in message_history]
            if actual_prefixes != expected_prefixes:
                return False
        return True

    def _generate_normal_response(self, message_history: list[dict]) -> str:
        raise NotImplementedError(
            "Subclasses must implement __generate_normal_response"
        )

    def _generate_structured_response(
        self, message_history: list[dict], response_model: BaseModel
    ) -> str:
        raise NotImplementedError(
            "Subclasses must implement _generate_structured_response"
        )

    def generate_response(
        self,
        query: str,
        message_history: list[dict] = [],
        response_model=str,
        system_prompt: str = "",
    ) -> str:
        # if not self.__validate_message_history(message_history):
        #     raise ValueError("Invalid message history")

        # Add the new message to the message history
        if len(system_prompt) > 0:
            message_history.append({"role": "system", "content": system_prompt})

        message_history.append({"role": self.user_prefix, "content": query})

        response = None

        llm_start_time = time.time()
        if response_model is str:
            response = self._generate_normal_response(message_history)
        else:
            response = self._generate_structured_response(
                message_history, response_model
            )
        llm_end_time = time.time()
        llm_duration = llm_end_time - llm_start_time
        print(f"LLM generated response in {llm_duration} seconds")

        if response is None:
            raise ValueError(f"Response is None for agent {self.agent_name}")

        return response

    def _generate_tool_call_response(self, message_history: list[dict], tools: list[dict]) -> str:
        raise NotImplementedError(
            "Subclasses must implement _generate_tool_call_response"
        )
