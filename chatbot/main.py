import asyncio
import atexit
import json
import os
import argparse

from pathlib import Path

from langchain.memory import ConversationBufferMemory, ChatMessageHistory
from langchain.llms import OpenAI
from langchain import ConversationChain, PromptTemplate
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

from langchain.schema import messages_from_dict, messages_to_dict

from config import DEFAULT_TEMPLATE, Prompt, WELCOME_MESSAGE, DATA_STRUCTURE, PREMIUM_MESSAGE, LIMIT_MESSAGE, \
    ERROR_MESSAGE
from utils import load_roles_from_file, load_user_roles, save_user_roles
from translate import translate

DATABASE_DIR = Path(__file__).parent / "database"
ROLES_FILE = "config/roles.json"
USER_ROLES_FILE = "user_roles.json"

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--telegram_token", help="Telegram bot token", type=str, required=True
    )
    args = parser.parse_args()
    return args


args = parse_args()

bot = Bot(token=args.telegram_token)
storage = MemoryStorage()

dispatcher = Dispatcher(bot, storage=storage, loop=asyncio.get_event_loop())

LLM = OpenAI(model_name="gpt-3.5-turbo", stop=["\nHuman:"])


# Load roles from the JSON file
ROLES = load_roles_from_file(ROLES_FILE)

# Load user roles at the start of your program
USER_ROLES = load_user_roles(user_roles_file=USER_ROLES_FILE)


@dispatcher.message_handler(commands=["career_assistant", "psychotherapist", "main_assistant"])
async def set_role(message: types.Message):
    user_id = str(message.from_user.id)
    command = message.get_command()

    # Find the role corresponding to the command
    role = next((r for r in ROLES if r["command"] == command), None)

    if role:
        USER_ROLES[user_id] = role["name"]

        # Save user roles
        save_user_roles(user_roles_file=USER_ROLES_FILE, user_roles=USER_ROLES)

        await bot.send_message(message.from_user.id, text=f"Включена роль : {role['name']}")
    else:
        await bot.send_message(message.from_user.id, text="Неправильная команда")


@dispatcher.message_handler(commands=["buy"])
async def show_message_count(message: types.Message):
    await bot.send_chat_action(message.from_user.id, action=types.ChatActions.TYPING)
    await bot.send_message(message.from_user.id, text=PREMIUM_MESSAGE)


@dispatcher.message_handler(commands=["free"])
async def show_message_count(message: types.Message):
    await bot.send_chat_action(message.from_user.id, action=types.ChatActions.TYPING)
    user_id = str(message.from_user.id)
    # Load message counts from a JSON file (if it exists)
    if os.path.isfile("message_counts.json"):
        # If it exists, load the data from the file
        with open("message_counts.json", "r") as f:
            USER_TO_CONVERSATION_ID = json.load(f)
    else:
        USER_TO_CONVERSATION_ID = {}
        # If it doesn't exist, create an empty dictionary
        await bot.send_message(user_id, text=ERROR_MESSAGE)
    print(USER_TO_CONVERSATION_ID)
    count = USER_TO_CONVERSATION_ID[user_id]
    remaining = 50 - int(count)
    await bot.send_message(user_id, text=f"У тебя осталось {remaining} бесплатных сообщений.")


@dispatcher.message_handler(commands=["start"])
async def start(message: types.Message):
    await bot.send_chat_action(message.from_user.id, action=types.ChatActions.TYPING)
    if not os.path.isdir(DATABASE_DIR):
        os.mkdir(DATABASE_DIR)

    if not os.path.isfile(DATABASE_DIR / f"{message.from_user.id}.json"):
        with open(DATABASE_DIR / f"{message.from_user.id}.json", 'w', encoding="utf-8") as f:
            json.dump(DATA_STRUCTURE, f)

    await bot.send_message(message.from_user.id, text=WELCOME_MESSAGE)


@dispatcher.message_handler()
async def handle_message(message: types.Message) -> None:
    translated_message = translate(message.text, from_lang="ru", to_lang="en")

    # Load message counts from a JSON file (if it exists)
    if os.path.isfile("message_counts.json"):
        # If it exists, load the data from the file
        with open("message_counts.json", "r") as f:
            USER_TO_CONVERSATION_ID = json.load(f)
    else:
        # If it doesn't exist, create an empty dictionary
        USER_TO_CONVERSATION_ID = {}
        await bot.send_message(message.from_user.id, text=ERROR_MESSAGE)

    user_id = str(message.from_user.id)

    # Get the current role for the user or default to None if not set
    current_role = USER_ROLES.get(user_id)

    # Check if user ID exists in the dictionary
    if user_id in USER_TO_CONVERSATION_ID:
        # Increment message count for the user
        USER_TO_CONVERSATION_ID[user_id] = int(USER_TO_CONVERSATION_ID[user_id]) + 1
    else:
        # Add user ID to the dictionary with an initial count of 1
        USER_TO_CONVERSATION_ID[user_id] = 1

    # Check if message count for the user exceeds 50
    if int(USER_TO_CONVERSATION_ID[user_id]) > 50:
        await bot.send_message(message.from_user.id, text=LIMIT_MESSAGE)
        with open("message_counts.json", "w") as f:
            json.dump(USER_TO_CONVERSATION_ID, f)
        return

    # Load the data from the file history
    if os.path.isfile(DATABASE_DIR / f"{message.from_user.id}.json"):
        with open(DATABASE_DIR / f"{message.from_user.id}.json", "r", encoding="utf-8") as f:
            json_string = f.read()
            # Parse the JSON data from the string
            retrieved_from_db = json.loads(json_string)

        retrieved_messages = messages_from_dict(retrieved_from_db)
        retrieved_chat_history = ChatMessageHistory(messages=retrieved_messages)
        retrieved_memory = ConversationBufferMemory(chat_memory=retrieved_chat_history)

        if current_role:
            # Find the role prompt for the current role
            role_prompt = next((r["prompt"] for r in ROLES if r["name"] == current_role), "")
            Prompt.prompt = role_prompt
            print(Prompt.prompt)
        else:
            Prompt.prompt = DEFAULT_TEMPLATE

        PROMPT = PromptTemplate(input_variables=["history", "input"], template=Prompt.prompt)
        reloaded_chain = ConversationChain(
            llm=LLM,
            verbose=True,
            memory=retrieved_memory,
            prompt=PROMPT,
        )
        await bot.send_chat_action(message.from_user.id, action=types.ChatActions.TYPING)
        chatbot_response = reloaded_chain.run(input=translated_message)
        translated_chatbot_response = translate(chatbot_response, from_lang="en", to_lang="ru")
        await bot.send_chat_action(message.from_user.id, action=types.ChatActions.TYPING)
        await bot.send_message(message.from_user.id, text=translated_chatbot_response)
        with open(DATABASE_DIR / f"{message.from_user.id}.json", "w") as f:
            json.dump(USER_TO_CONVERSATION_ID, f)

        extracted_messages = reloaded_chain.memory.chat_memory.messages
        ingest_to_db = messages_to_dict(extracted_messages)
        # Save the data to the file with new messages
        with open(DATABASE_DIR / f"{message.from_user.id}.json", "w", encoding="utf-8") as f:
            json.dump(ingest_to_db, f)
        # Update counts of messages
        with open("message_counts.json", "w") as f:
            json.dump(USER_TO_CONVERSATION_ID, f)
    else:

        await bot.send_message(user_id, text=ERROR_MESSAGE)


# Save user roles before the bot exits
atexit.register(save_user_roles, user_roles_file=USER_ROLES_FILE, user_roles=USER_ROLES)

# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    executor.start_polling(dispatcher, skip_updates=False)
