DEFAULT_TEMPLATE = """The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know. The AI tries to present its thoughts in a structured way, dividing the text into paragraphs for easy reading

Current conversation:
{history}
Human: {input}
AI:"""

PREMIUM_MESSAGE = """Премиум:
- безлимитный доступ и общение с телеграм-ботом
- подписка на все обновления
- приоритетная поддержка
490 руб/мес. - оплатить"""

WELCOME_MESSAGE = """ Привет! Я ИИ-компаньон chatGPT. Помогу тебе с рабочими задачами, генерацией контента и идей!

Подпишись на наш канал, чтобы быть в курсе обновлений и новостей из мира нейросетей - https://t.me/neurocompanion

Если у тебя есть идеи по развитию бота или вопросы, пиши @ilyaberdysh

Давай знакомиться, спроси у меня что-нибудь """

ERROR_MESSAGE = "Привет! Чтобы запустить бота, нажми команду /start"

LIMIT_MESSAGE = """ К сожалению, твой лимит бесплатный сообщений закончился. 
Напиши @ilyaberdysh, чтобы оплатить платный тариф (490 рублей - безлимит в месяц) и продолжить общение!"""

DATA_STRUCTURE = [
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


class Prompt:
    prompt = DEFAULT_TEMPLATE
