import os
import logging
import random
from datetime import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from telegram.ext import CallbackContext
from telegram.ext import JobQueue
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
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

# Выбор часового пояса
CITIES = {
    "Тбилиси": 4,
    "Москва": 3,
    "Киев": 3,
    "Самара": 4,
    "Рим": 2,
    "Барселона": 2,
    "Лондон": 1
}

# Цитаты
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, tz in subscribers.items():
        quote = random.choice(QUOTES)
        try:
            await context.bot.send_message(chat_id=chat_id, text=quote, parse_mode='HTML')
            logger.info(f"Цитата отправлена в {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке цитаты: {e}")

# Рефлексия
REFLECTION_TEXT = (
    "<b>🧘‍♂️ Стоическая неделя. Время для размышлений.</b>\n"
    "Эти вопросы не для галочки. Найди несколько минут тишины, чтобы честно взглянуть на прожитую неделю. "
    "Ответы не обязательны — но они могут многое изменить в твоей жизни.\n\n"
    "1️⃣ В каких ситуациях на этой неделе я позволил эмоциям взять верх над разумом, и как мог бы отреагировать более мудро, мужественно, справедливо и умеренно?\n\n"
    "2️⃣ Какие мои действия действительно соответствовали стоическим ценностям и принципам, а какие шли вразрез с ними?\n\n"
    "3️⃣ Что из того, что я считал важным на этой неделе, действительно будет иметь значение через год?\n\n"
    "4️⃣ Какие возможности послужить другим людям я упустил на этой неделе?\n\n"
    "5️⃣ Какие препятствия и трудности этой недели я смог превратить в возможности для роста, а какие уроки упустил?"
)

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id=chat_id, text=REFLECTION_TEXT, parse_mode='HTML')
            logger.info(f"Рефлексия отправлена в {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка рефлексии: {e}")

# Обработка выбора города
async def handle_city_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id
    city = query.data
    tz = CITIES[city]
    subscribers[chat_id] = tz
    await query.edit_message_text(
        text=f"✅ Вы выбрали: {city}. Цитаты будут приходить каждый день в 9:00 по вашему времени."
    )
    logger.info(f"Подписался: {chat_id} (часовой пояс UTC+{tz})")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(city, callback_data=city)] for city in CITIES]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👇 Пожалуйста, выбери город из списка, используй кнопки:",
        reply_markup=reply_markup
    )

# /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        del subscribers[chat_id]
        await update.message.reply_text("❌ Вы отписаны.")
    else:
        await update.message.reply_text("Вы и так не подписаны.")

# main
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CallbackQueryHandler(handle_city_selection))

    app.job_queue.run_repeating(send_quote, interval=30, first=5)
    app.job_queue.run_repeating(send_reflection, interval=30, first=15)

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
