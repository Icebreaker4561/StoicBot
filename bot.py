import os
import logging
import random
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from stoic_quotes_100 import QUOTES

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = os.getenv("BOT_TOKEN")

# Subscribers: chat_id -> timezone string
subscribers = {}

# Mapping city names to timezones
CITY_TZ = {
    "Москва": "Europe/Moscow",
    "Тбилиси": "Asia/Tbilisi",
    "Рим": "Europe/Rome",
    "Барселона": "Europe/Madrid",
    "Лондон": "Europe/London",
    "Киев": "Europe/Kyiv",
    "Самара": "Europe/Samara"
}

# Scheduled job: runs every minute
async def scheduled_task(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, tz_name in subscribers.items():
        try:
            tz = ZoneInfo(tz_name)
            now = datetime.now(tz)
            # Send quote at 09:00
            if now.hour == 9 and now.minute == 0:
                quote = random.choice(QUOTES)
                await context.bot.send_message(chat_id, quote)
                logger.info(f"Sent quote to {chat_id} at {now.time()} [{tz_name}]")
            # Send reflection on Sunday (weekday=6) at 12:00
            if now.weekday() == 6 and now.hour == 12 and now.minute == 0:
                reflection = (
                    "🧘‍♂️ Стоическая неделя. Время для размышлений.\n"
                    "Эти вопросы не для галочки. Найди несколько минут тишины...\n"
                    "1️⃣ В каких ситуациях я позволил эмоциям взять верх над разумом...\n"
                    "2️⃣ Какие мои действия соответствовали стоическим ценностям...\n"
                    "3️⃣ Что из того, что я считал важным на этой неделе,\n    будет иметь значение через год?\n"
                    "4️⃣ Какие возможности послужить другим людям я упустил?\n"
                    "5️⃣ Какие препятствия я смог превратить в рост,\n    а какие уроки упустил?"
                )
                await context.bot.send_message(chat_id, reflection)
                logger.info(f"Sent reflection to {chat_id} at {now.time()} [{tz_name}]")
        except Exception as e:
            logger.error(f"Error scheduling for {chat_id}: {e}")

# /start command: ask to choose city
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[city] for city in CITY_TZ.keys()]
    await update.message.reply_text(
        "Пожалуйста, выберите свой город из списка:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )
    logger.info(f"Asking city for {update.effective_chat.id}")

# Handle city selection
async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    city = update.message.text.strip()
    if city in CITY_TZ:
        subscribers[chat_id] = CITY_TZ[city]
        await update.message.reply_text(
            f"✅ Готово!\nТеперь Вы будете получать одну мысль из стоицизма каждое утро в 9:00.\n"
            f"\n🔔 Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения."
        )
        logger.info(f"Subscribed {chat_id} with TZ {CITY_TZ[city]}")
    else:
        await update.message.reply_text(
            "Город не распознан, попробуйте еще раз."
        )
        logger.warning(f"Unknown city from {chat_id}: {city}")

# /stop command: unsubscribe
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.pop(chat_id, None)
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
        logger.info(f"Unsubscribed {chat_id}")
    else:
        await update.message.reply_text("Вы не были подписаны.")

# Main function
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_city))

    app.job_queue.run_repeating(scheduled_task, interval=60, first=10)

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
