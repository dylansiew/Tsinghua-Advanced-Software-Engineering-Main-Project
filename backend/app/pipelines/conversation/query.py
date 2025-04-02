import asyncio
from datetime import datetime

from app.genai.llm import llm_agent
from app.genai.tts import tts_agent
from app.utils.db import message_db
from fastapi.responses import FileResponse
from models.conversation.message import Message
from models.conversation.role import MessageRole


async def save_messages(conversation_id: str, query: str, llm_response: str):
    user_message = Message(
        conversation_id=conversation_id,
        created_at=datetime.now(),
        message_role=MessageRole.USER,
        message_content=query
    )
    assistant_message = Message(
        conversation_id=conversation_id,
        created_at=datetime.now(),
        message_role=MessageRole.ASSISTANT,
        message_content=llm_response
    )
    message_db.insert_message(user_message)
    message_db.insert_message(assistant_message)


async def talk_to_llm(conversation_id: str, query: str):
    messages = message_db.get_all_messages(conversation_id)
    formatted_messages = [message.to_gpt_message() for message in messages]

    system_prompt_filepath = "app/genai/llm/prompts/Tasha/system.txt"
    with open(system_prompt_filepath, "r") as file:
        system_prompt = file.read()

    llm_response = llm_agent.generate_response(
        query=query,
        message_history=formatted_messages,
        response_model=str,
        system_prompt=system_prompt
    )

    # Fire-and-forget background task to save messages
    asyncio.create_task(save_messages(conversation_id, query, llm_response))

    tts_output_filepath = f"data/tts/output/{conversation_id}.mp3"
    tts_success = tts_agent.convert_text_to_speech(text=llm_response, output_file=tts_output_filepath)
    if not tts_success:
        print("Failed to generate TTS")
        return None

    return FileResponse(tts_output_filepath)


