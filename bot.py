import os
import logging
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters
)
from telegram.constants import ParseMode
from stoic_quotes_100 import QUOTES

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
subscribers = {}  # chat_id: timezone_offset

CITIES = {
    "Тбилиси": 4,
    "Москва": 3,
    "Киев": 3,
    "Самара": 4,
    "Рим": 2,
    "Барселона": 2,
    "Лондон": 1
}

def build_timezone_keyboard():
    keyboard = [[InlineKeyboardButton(city, callback_data=city)] for city in CITIES]
    return InlineKeyboardMarkup(keyboard)

async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    now_utc = datetime.utcnow()
    for chat_id, offset in subscribers.items():
        user_time = now_utc + timedelta(hours=offset)
        if user_time.minute % 2 == 0:
            quote = random.choice(QUOTES)
            try:
                await context.bot.send_message(chat_id=chat_id, text=quote, parse_mode=ParseMode.HTML)
                logger.info(f"Цитата отправлена в {chat_id} в {user_time.strftime('%H:%M')} по локальному времени")
            except Exception as e:
                logger.error(f"Ошибка при отправке цитаты: {e}")

REFLECTION_TEXT = (
    "<b>🧘‍♂️ Стоическая неделя. Время для размышлений.</b>\n\n"
    "Эти вопросы не для галочки. Найди несколько минут тишины, чтобы честно взглянуть на прожитую неделю. Ответы не обязательны — но они могут многое изменить в твоей жизни.\n\n"
    "1️⃣ В каких ситуациях на этой неделе я позволил эмоциям взять верх над разумом, и как мог бы отреагировать более мудро, мужественно, справедливо и умеренно?\n\n"
    "2️⃣ Какие мои действия действительно соответствовали стоическим ценностям и принципам, а какие шли вразрез с ними?\n\n"
    "3️⃣ Что из того, что я считал важным на этой неделе, действительно будет иметь значение через год?\n\n"
    "4️⃣ Какие возможности послужить другим людям я упустил на этой неделе?\n\n"
    "5️⃣ Какие препятствия и трудности этой недели я смог превратить в возможности для роста, а какие уроки упустил?"
)

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    now_utc = datetime.utcnow()
    for chat_id, offset in subscribers.items():
        user_time = now_utc + timedelta(hours=offset)
        if user_time.minute % 2 == 1:
            try:
                await context.bot.send_message(chat_id=chat_id, text=REFLECTION_TEXT, parse_mode=ParseMode.HTML)
                logger.info(f"Рефлексия отправлена в {chat_id} в {user_time.strftime('%H:%M')} по локальному времени")
            except Exception as e:
                logger.error(f"Ошибка рефлексии: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        "✅ Вы подписаны на стоические цитаты и рефлексию.\n\n👇 Пожалуйста, выбери город, чтобы настроить время доставки:",
        reply_markup=build_timezone_keyboard()
    )
    logger.info(f"Пользователь {chat_id} начал регистрацию")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        del subscribers[chat_id]
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
    else:
        await update.message.reply_text("Вы не были подписаны.")

async def select_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    city = query.data
    chat_id = query.message.chat.id
    offset = CITIES[city]
    subscribers[chat_id] = offset
    await query.edit_message_text(f"🌍 Часовой пояс {city} (UTC+{offset}) выбран. Рассылка активирована.")
    logger.info(f"Пользователь {chat_id} выбрал город {city} с UTC+{offset}")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CallbackQueryHandler(select_timezone))

    app.job_queue.run_repeating(send_quote, interval=60, first=0)
    app.job_queue.run_repeating(send_reflection, interval=60, first=15)

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
