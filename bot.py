import os
import logging
import random
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
from zoneinfo import ZoneInfo
from stoic_quotes_100 import QUOTES

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Переменные
TOKEN = os.getenv("BOT_TOKEN")
subscribers = {}

# Список городов и часовых поясов
CITY_TIMEZONES = {
    "Тбилиси": "Asia/Tbilisi",
    "Москва": "Europe/Moscow",
    "Киев": "Europe/Kyiv",
    "Самара": "Europe/Samara",
    "Барселона": "Europe/Madrid",
    "Рим": "Europe/Rome",
    "Лондон": "Europe/London"
}

# Выбор города
async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[city] for city in CITY_TIMEZONES.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("👇 Пожалуйста, выбери город из списка:", reply_markup=reply_markup)

# Обработка выбора города
async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    if city in CITY_TIMEZONES:
        chat_id = update.effective_chat.id
        tz = CITY_TIMEZONES[city]
        subscribers[chat_id] = tz
        await update.message.reply_text(f"✅ Город установлен: {city}. Часовой пояс — {tz}")
    else:
        await update.message.reply_text("❌ Пожалуйста, выбери город из списка.")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in subscribers:
        subscribers[chat_id] = "Europe/Moscow"
    await update.message.reply_text("✅ Вы подписаны на стоические цитаты и еженедельную рефлексию.")

# Команда /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        del subscribers[chat_id]
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
    else:
        await update.message.reply_text("Вы не были подписаны.")

# Цитата
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    quote = random.choice(QUOTES)
    for chat_id, tz in subscribers.items():
        now = datetime.now(ZoneInfo(tz))
        if now.minute % 2 == 0:  # Каждая чётная минута
            try:
                await context.bot.send_message(chat_id=chat_id, text=quote, parse_mode='HTML')
                logger.info(f"Цитата отправлена в {chat_id}")
            except Exception as e:
                logger.error(f"Ошибка при отправке цитаты: {e}")

# Рефлексия
REFLECTION_TEXT = (
    "🧘‍♂️ Стоическая неделя. Время для размышлений.\n\n"
    "Эти вопросы не для галочки. Найди несколько минут тишины, чтобы честно взглянуть на прожитую неделю."
    " Ответы не обязательны — но они могут многое изменить в твоей жизни.\n\n"
    "1️⃣ В каких ситуациях на этой неделе я позволил эмоциям взять верх над разумом, и как мог бы отреагировать более мудро, мужественно, справедливо и умеренно?\n"
    "2️⃣ Какие мои действия действительно соответствовали стоическим ценностям и принципам, а какие шли вразрез с ними?\n"
    "3️⃣ Что из того, что я считал важным на этой неделе, действительно будет иметь значение через год?\n"
    "4️⃣ Какие возможности послужить другим людям я упустил на этой неделе?\n"
    "5️⃣ Какие препятствия и трудности этой недели я смог превратить в возможности для роста, а какие уроки упустил?"
)

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, tz in subscribers.items():
        now = datetime.now(ZoneInfo(tz))
        if now.minute % 2 == 1:  # Каждая нечётная минута
            try:
                await context.bot.send_message(chat_id=chat_id, text=REFLECTION_TEXT, parse_mode='HTML')
                logger.info(f"Рефлексия отправлена в {chat_id}")
            except Exception as e:
                logger.error(f"Ошибка при отправке рефлексии: {e}")

# Запуск
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("setcity", set_city))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_quote, "interval", seconds=30, args=[app.bot])
    scheduler.add_job(send_reflection, "interval", seconds=30, args=[app.bot])
    scheduler.start()

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
