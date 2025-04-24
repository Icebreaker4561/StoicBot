from telegram import Bot
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
import pytz
import random

# Твои данные (засветились ранее — позже лучше заменить токен)
TOKEN = '7663921238:AAGZaEqkIjvadZE-2hbI2avn6a7asafZM8c'
CHAT_ID = 328758295

QUOTES = [
    "Жизнь не коротка, но мы делаем её таковой. — Сенека",
    "Не вещи беспокоят людей, а мнение о вещах. — Эпиктет",
    "Будь безупречен в настоящем. — Марк Аврелий",
    "Пока мы откладываем жизнь, она проходит. — Сенека",
    "Начни жить немедленно и считай каждый день за отдельную жизнь. — Сенека",
    "Счастье — это не удовольствие, а свобода от страданий. — Эпиктет",
    "Пока ты жив — учись жить. — Сенека",
    "Ты поступаешь, как смертный, в том, чего боишься, и как бессмертный — в том, чего жаждешь. — Сенека"
]

def send_quote():
    bot = Bot(token=TOKEN)
    quote = random.choice(QUOTES)
    bot.send_message(chat_id=CHAT_ID, text=quote)

scheduler = BlockingScheduler(timezone=pytz.utc)
scheduler.add_job(send_quote, IntervalTrigger(minutes=1, timezone=pytz.utc))  # Тест: цитата каждую минуту
scheduler.start()