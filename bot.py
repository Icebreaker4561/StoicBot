import os
import logging
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from stoic_quotes_100 import QUOTES

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Переменные
TOKEN = os.getenv("BOT_TOKEN")
TIMEZONES = {
    "Лондон": 0,
    "Рим": 2,
    "Барселона": 2,
    "Киев": 3,
    "Москва": 3,
    "Самара": 4,
    "Тбилиси": 4
}
users = {}

# Цитаты
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    from datetime import datetime, timedelta
    now_utc = datetime.utcnow()
    for chat_id, tz_offset in users.items():
        user_time = now_utc + timedelta(hours=tz_offset)
        if user_time.second % 30 == 0:
            quote = random.choice(QUOTES)
            try:
                await context.bot.send_message(chat_id=chat_id, text=quote, parse_mode='HTML')
                logger.info(f"Цитата отправлена в {chat_id}")
            except Exception as e:
                logger.error(f"Ошибка при отправке цитаты: {e}")

# Рефлексия
REFLECTION_TEXT = (
    "<b>🧘‍♂️ Стоическая неделя. Время для размышлений.</b>\n\n"
    "Эти вопросы не для галочки. Найди несколько минут тишины, чтобы честно взглянуть на прожитую неделю. "
    "Ответы не обязательны — но они могут многое изменить в твоей жизни.\n\n"
    "1️⃣ В каких ситуациях на этой неделе я позволил эмоциям взять верх над разумом, и как мог бы отреагировать более мудро, мужественно, справедливо и умеренно?\n\n"
    "2️⃣ Какие мои действия действительно соответствовали стоическим ценностям и принципам, а какие шли вразрез с ними?\n\n"
    "3️⃣ Что из того, что я считал важным на этой неделе, действительно будет иметь значение через год?\n\n"
    "4️⃣ Какие возможности послужить другим людям я упустил на этой неделе?\n\n"
    "5️⃣ Какие препятствия и трудности этой недели я смог превратить в возможности для роста, а какие уроки упустил?"
)

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    from datetime import datetime, timedelta
    now_utc = datetime.utcnow()
    for chat_id, tz_offset in users.items():
        user_time = now_utc + timedelta(hours=tz_offset)
        if user_time.second % 30 == 15:
            try:
                await context.bot.send_message(chat_id=chat_id, text=REFLECTION_TEXT, parse_mode='HTML')
                logger.info(f"Рефлексия отправлена в {chat_id}")
            except Exception as e:
                logger.error(f"Ошибка рефлексии: {e}")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[city] for city in TIMEZONES.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "⏰ Чтобы получать стоические цитаты и рефлексию, выбери ближайший к тебе город:",
        reply_markup=reply_markup
    )

# Обработка выбора города
async def handle_city_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_city = update.message.text
    chat_id = update.message.chat_id
    if user_city in TIMEZONES:
        users[chat_id] = TIMEZONES[user_city]
        await update.message.reply_text(f"✅ Вы выбрали {user_city}. Цитаты и рефлексия будут приходить по местному времени.")
        logger.info(f"Подписан: {chat_id} (часовой пояс {TIMEZONES[user_city]})")
    else:
        await update.message.reply_text("Пожалуйста, выбери город из предложенного списка.")

# /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in users:
        del users[chat_id]
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
        logger.info(f"Отписался: {chat_id}")
    else:
        await update.message.reply_text("Вы не были подписаны.")

# main
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city_choice))

    app.job_queue.run_repeating(send_quote, interval=30, first=5)
    app.job_queue.run_repeating(send_reflection, interval=30, first=15)

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
