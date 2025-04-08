import asyncio
import base64
import json
from datetime import datetime

from app.genai.llm import llm_agent
from app.genai.tts import tts_agent
from app.utils.db import message_db
from app.utils.ws import conversation_ws_manager
from fastapi.responses import FileResponse
from models.conversation.conversation import (
    AudioMessage,
    ConversationMessage,
    ConversationMessageType,
    QueryMessage,
)
from models.conversation.message import Message
from models.conversation.role import MessageRole
from models.tts.viseme import AudioData


async def save_messages(conversation_id: str, query: str, llm_response: str):
    user_message = Message(
        conversation_id=conversation_id,
        created_at=datetime.now(),
        message_role=MessageRole.USER,
        message_content=query,
    )
    assistant_message = Message(
        conversation_id=conversation_id,
        created_at=datetime.now(),
        message_role=MessageRole.ASSISTANT,
        message_content=llm_response,
    )
    message_db.insert_message(user_message)
    message_db.insert_message(assistant_message)


async def create_response(audio_response: AudioMessage):
    response = ConversationMessage(
        type=ConversationMessageType.AUDIO_RESPONSE, data=audio_response
    )
    return response


cache = "cache.json"


async def talk_to_llm(conversation_id: str, query: QueryMessage):
    # print(f"{query=}")
    # with open(cache, "r") as file:
    #     cache_data = json.load(file)

    #     response = ConversationMessage(
    #         type=ConversationMessageType.AUDIO_RESPONSE,
    #         data=AudioMessage(**cache_data["data"]),
    #     )
    # await conversation_ws_manager.send_personal_message(
    #     message=response, user_id=conversation_id
    # )
    # return
    messages = message_db.get_all_messages(conversation_id)
    formatted_messages = [message.to_gpt_message() for message in messages]

    print(f"{formatted_messages=}")

    system_prompt_filepath = "app/genai/llm/prompts/Tasha/system.txt"
    with open(system_prompt_filepath, "r") as file:
        system_prompt = file.read()

    llm_response = llm_agent.generate_response(
        query=query.query,
        message_history=formatted_messages,
        response_model=str,
        system_prompt=system_prompt,
    )

    # Fire-and-forget background task to save messages
    asyncio.create_task(save_messages(conversation_id, query.query, llm_response))

    # await conversation_ws_manager.send_personal_message(
    #     message=llm_response, user_id=conversation_id
    # )

    tts_output_filepath = f"data/tts/output/{conversation_id}.mp3"
    audio_response = tts_agent.convert_text_to_speech(
        text=llm_response, output_file=tts_output_filepath
    )
    if not audio_response:
        print("Failed to generate TTS")
        return None

    response = await create_response(audio_response)

    json_data = {"type": "audio_response", "data": audio_response.model_dump()}

    with open(cache, "w") as file:
        json.dump(json_data, file)

    await conversation_ws_manager.send_personal_message(
        message=response, user_id=conversation_id
    )
