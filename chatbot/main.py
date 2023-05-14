import asyncio
import json
import os
from pathlib import Path
from langchain.memory import ConversationBufferMemory, ChatMessageHistory
from langchain.llms import OpenAI
from langchain import ConversationChain
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

from langchain.schema import messages_from_dict, messages_to_dict

DATABASE_DIR = Path(__file__).parent / "database"

token = "5884042159:AAF1Mc47CyEkXLhYPKrdYQGXfWWcpIB1qNk"
bot = Bot(token=token)  # args.telegram_token
storage = MemoryStorage()

dispatcher = Dispatcher(bot, storage=storage, loop=asyncio.get_event_loop())

llm = OpenAI(model_name="gpt-3.5-turbo")
conversation = ConversationChain(
    llm=llm,
    verbose=True,
    memory=ConversationBufferMemory()
)

@dispatcher.message_handler(commands=["free"])
async def show_message_count(message: types.Message):
    user_id = str(message.from_user.id)
    # Load message counts from a JSON file (if it exists)
    if os.path.isfile("message_counts.json"):
        # If it exists, load the data from the file
        with open("message_counts.json", "r") as f:
            USER_TO_CONVERSATION_ID = json.load(f)
    else:
        USER_TO_CONVERSATION_ID = {}
        # If it doesn't exist, create an empty dictionary
        await bot.send_message(user_id, text="Привет! Чтобы запустить бота, нажми команду /start")
    print(USER_TO_CONVERSATION_ID)
    count = USER_TO_CONVERSATION_ID[user_id]
    remaining = 50 - int(count)
    await bot.send_message(user_id, text=f"У тебя осталось {remaining} бесплатных сообщений.")


@dispatcher.message_handler(commands=["start"])
async def start(message: types.Message):
    data = [
        {
            'type': 'human',
            'data': {
                'content': '',
                'additional_kwargs': {}
            }
        },
        {
            'type': 'ai',
            'data': {
                'content': '',
                'additional_kwargs': {}
            }
        }
    ]
    if not os.path.isdir(DATABASE_DIR):
        os.mkdir(DATABASE_DIR)
    with open(DATABASE_DIR/f"{message.from_user.id}.json", 'w', encoding="utf-8") as f:
        json.dump(data, f)

    await bot.send_message(message.from_user.id, text=""" Привет! Я ИИ-компаньон chatGPT. Помогу тебе с рабочими задачами, генерацией контента и идей!

Подпишись на наш канал, чтобы быть в курсе обновлений и новостей из мира нейросетей - https://t.me/neurocompanion

Если у тебя есть идеи по развитию бота или вопросы, пиши @ilyaberdysh

Давай знакомиться, спроси у меня что-нибудь """)


@dispatcher.message_handler()
async def handle_message(message: types.Message) -> None:
    # Load message counts from a JSON file (if it exists)
    if os.path.isfile("message_counts.json"):
        # If it exists, load the data from the file
        with open("message_counts.json", "r") as f:
            USER_TO_CONVERSATION_ID = json.load(f)
    else:
        # If it doesn't exist, create an empty dictionary
        USER_TO_CONVERSATION_ID = {}
        await bot.send_message(message.from_user.id, text="Привет! Чтобы запустить бота, нажми команду /start")

    user_id = str(message.from_user.id)

    # Check if user ID exists in the dictionary
    if user_id in USER_TO_CONVERSATION_ID:
        # Increment message count for the user
        USER_TO_CONVERSATION_ID[user_id] = int(USER_TO_CONVERSATION_ID[user_id]) + 1
    else:
        # Add user ID to the dictionary with an initial count of 1
        USER_TO_CONVERSATION_ID[user_id] = 1

    # Check if message count for the user exceeds 100
    if int(USER_TO_CONVERSATION_ID[user_id]) > 50:
        await bot.send_message(message.from_user.id, text=""" К сожалению, твой лимит бесплатный сообщений закончился. 
Напиши @ilyaberdysh, чтобы оплатить платный тариф (500 рублей - безлимит в месяц) и продолжить общение!""")
        with open("message_counts.json", "w") as f:
            json.dump(USER_TO_CONVERSATION_ID, f)
        return

    if os.path.isfile(DATABASE_DIR/f"{message.from_user.id}.json"):
        with open(DATABASE_DIR/f"{message.from_user.id}.json", "r", encoding="utf-8") as f:
            json_string = f.read()
            # Parse the JSON data from the string
            retrieved_from_db = json.loads(json_string)
        retrieved_messages = messages_from_dict(retrieved_from_db)
        retrieved_chat_history = ChatMessageHistory(messages=retrieved_messages)
        retrieved_memory = ConversationBufferMemory(chat_memory=retrieved_chat_history)
        reloaded_chain = ConversationChain(
            llm=llm,
            verbose=True,
            memory=retrieved_memory
        )
        chatbot_response = reloaded_chain.run(input=message.text)
        await bot.send_message(message.from_user.id, text=chatbot_response)
        with open(DATABASE_DIR/f"{message.from_user.id}.json", "w") as f:
            json.dump(USER_TO_CONVERSATION_ID, f)

        extracted_messages = reloaded_chain.memory.chat_memory.messages
        ingest_to_db = messages_to_dict(extracted_messages)
        with open(DATABASE_DIR/f"{message.from_user.id}.json", "w", encoding="utf-8") as f:
            json.dump(ingest_to_db, f)
    else:

        await bot.send_message(user_id, text="Привет! Чтобы запустить бота, нажми команду /start")


# Press the green button in the gutter to run the script.
if __name__ == "__main__":

    executor.start_polling(dispatcher, skip_updates=False)
