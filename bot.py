import os
import logging
import random
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackContext,
)
from telegram.ext import ConversationHandler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

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

# Список городов и их смещения по UTC
CITIES = {
    "Москва": 3,
    "Тбилиси": 4,
    "Киев": 3,
    "Самара": 4,
    "Лондон": 0,
    "Рим": 2,
    "Барселона": 2,
}
CITY_LIST = list(CITIES.keys())

# Состояния для ConversationHandler
CHOOSE_CITY = 1

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[city] for city in CITY_LIST]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("👇 Пожалуйста, выбери город, чтобы настроить локальное время.", reply_markup=reply_markup)
    return CHOOSE_CITY

# Выбор города
async def choose_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    city = update.message.text
    chat_id = update.effective_chat.id

    if city not in CITIES:
        await update.message.reply_text("Пожалуйста, выбери город из списка.")
        return CHOOSE_CITY

    tz_offset = CITIES[city]
    subscribers[chat_id] = tz_offset

    await update.message.reply_text(
        "✅ Готово! Вы будете получать стоические цитаты каждые 30 секунд.",
        parse_mode='HTML'
    )
    await update.message.reply_text(
        "🔔 <i>Telegram может по умолчанию отключать уведомления от ботов. Чтобы получать стоические цитаты — откройте настройки этого чата и включите уведомления.</i>",
        parse_mode='HTML'
    )
    logger.info(f"Подписан: {chat_id} в часовом поясе {tz_offset}")
    return ConversationHandler.END

# Команда /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        del subscribers[chat_id]
        await update.message.reply_text("❌ Вы отписаны.")
    else:
        await update.message.reply_text("Вы не были подписаны.")

# Цитата
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in subscribers:
        try:
            quote = random.choice(QUOTES)
            await context.bot.send_message(chat_id=chat_id, text=quote, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Ошибка при отправке цитаты: {e}")

# Рефлексия
REFLECTION_TEXT = (
    "🧠 <b>Недельная рефлексия</b>\n"
    "👉 <i>В каких ситуациях я позволил эмоциям взять верх, и как я мог бы отреагировать более мудро?</i>\n"
    "👉 <i>Какие мои действия соответствовали стоическим ценностям, а какие ему противоречили?</i>\n"
    "👉 <i>Что из этой недели будет иметь значение через год?</i>\n"
    "👉 <i>Когда я упустил шанс помочь другим?</i>\n"
    "👉 <i>Какие препятствия стали моим ростом?</i>"
)

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id=chat_id, text=REFLECTION_TEXT, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Ошибка при отправке рефлексии: {e}")

# Главная функция
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={CHOOSE_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_city)]},
        fallbacks=[]
    )
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("stop", stop))

    app.job_queue.run_repeating(send_quote, interval=30, first=10)
    app.job_queue.run_repeating(send_reflection, interval=30, first=20)

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
