import asyncio
import json
import os


from langchain.memory import ConversationBufferMemory
from langchain.llms import OpenAI
from langchain import ConversationChain
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.types import BotCommand

token = "5884042159:AAF1Mc47CyEkXLhYPKrdYQGXfWWcpIB1qNk"
bot = Bot(token=token)  # args.telegram_token
storage = MemoryStorage()

dispatcher = Dispatcher(bot, storage=storage, loop=asyncio.get_event_loop())
#DEFAULT_KEYBOARD = types.ReplyKeyboardMarkup(
#    keyboard=[[KeyboardButton("/start")], [KeyboardButton("/free_messages")]],
#    resize_keyboard=True,
#    one_time_keyboard=True,
#)
llm = OpenAI(model_name="gpt-3.5-turbo")
conversation = ConversationChain(
    llm=llm,
    verbose=True,
    memory=ConversationBufferMemory()
)

# Load message counts from a JSON file (if it exists)
if os.path.isfile("message_counts.json"):
    # If it exists, load the data from the file
    with open("message_counts.json", "r") as f:
        USER_TO_CONVERSATION_ID = json.load(f)
else:
    # If it doesn't exist, create an empty dictionary
    USER_TO_CONVERSATION_ID = {}


@dispatcher.message_handler(commands=["free"])
async def show_message_count(message: types.Message):
    user_id = str(message.from_user.id)
    count = USER_TO_CONVERSATION_ID[user_id]
    remaining = 100 - int(count)
    await bot.send_message(user_id, text=f"У тебя осталось {remaining} бесплатных сообщений.")


@dispatcher.message_handler(commands=["start"])
async def start(message: types.Message):
    await bot.send_message(message.from_user.id, text=""" Привет! Я ИИ-компаньон chatGPT. Помогу тебе с рабочими задачами, генерацией контента и идей!

Подпишись на наш канал, чтобы быть в курсе обновлений и новостей из мира нейросетей - https://t.me/neurocompanion

Если у тебя есть идеи по развитию бота или вопросы, пиши @ilyaberdysh

Давай знакомиться, спроси у меня что-нибудь """)


@dispatcher.message_handler()
async def handle_message(message: types.Message) -> None:
    user_id = str(message.from_user.id)

    # Check if user ID exists in the dictionary
    if user_id in USER_TO_CONVERSATION_ID:
        # Increment message count for the user
        USER_TO_CONVERSATION_ID[user_id] += 1
    else:
        # Add user ID to the dictionary with an initial count of 1
        USER_TO_CONVERSATION_ID[user_id] = str(1)

    # Check if message count for the user exceeds 100
    if int(USER_TO_CONVERSATION_ID[user_id]) > 100:
        await bot.send_message(message.from_user.id, text=""" К сожалению, твой лимит бесплатный сообщений закончился. 
Напиши @ilyaberdysh, чтобы оплатить платный тариф (500 рублей - безлимит в месяц) и продолжить общение!""")
        with open("message_counts.json", "w") as f:
            json.dump(USER_TO_CONVERSATION_ID, f)
        return

    # Predict response using OpenAI model
    chatbot_response = conversation.predict(input=message.text)
    await bot.send_message(message.from_user.id, text=chatbot_response)
    print(USER_TO_CONVERSATION_ID)
    # Save message counts to a JSON file
    with open("message_counts.json", "w") as f:
        json.dump(USER_TO_CONVERSATION_ID, f)


# Press the green button in the gutter to run the script.
if __name__ == "__main__":

    executor.start_polling(dispatcher, skip_updates=False)
