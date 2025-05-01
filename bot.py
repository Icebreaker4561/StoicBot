import os
import logging
import random
from datetime import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from telegram.ext import JobQueue
from stoic_quotes_100 import QUOTES

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = os.getenv("BOT_TOKEN")

# Subscribers: chat_id -> timezone offset hours
subscribers = {}

# Weekly reflection text
REFLECTION_TEXT = (
    "🧘‍♂️ Стоическая неделя. Время для размышлений.\n"
    "Эти вопросы не для галочки. Найдите пару минут тишины и честно ответьте:\n"
    "1️⃣ В каких ситуациях на этой неделе я позволил эмоциям взять верх над разумом, и как мог бы отреагировать более мудро, мужественно, справедливо и умеренно?\n"
    "2️⃣ Какие мои действия действительно соответствовали стоическим ценностям и принципам, а какие им противоречили?\n"
    "3️⃣ Что из того, что я считал важным на этой неделе, действительно будет иметь значение через год?\n"
    "4️⃣ Какие возможности послужить другим людям я упустил на этой неделе?\n"
    "5️⃣ Какие препятствия и трудности этой недели я смог превратить в возможности для роста, а какие уроки упустил?"
)

async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, tz in subscribers.items():
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=random.choice(QUOTES),
                parse_mode='HTML'
            )
            logger.info(f"Quote sent to {chat_id}")
        except Exception as e:
            logger.error(f"Error sending quote to {chat_id}: {e}")

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, tz in subscribers.items():
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=REFLECTION_TEXT,
                parse_mode='HTML'
            )
            logger.info(f"Reflection sent to {chat_id}")
        except Exception as e:
            logger.error(f"Error sending reflection to {chat_id}: {e}")

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # Ask for timezone
    keyboard = [['Москва'], ['Киев'], ['Тбилиси'], ['Самара']]
    await update.message.reply_text(
        "✅ Готово!\n"
        "Теперь Вы будете получать одну мысль из стоицизма каждое утро в 9:00.\n\n"
        "🔔 Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения.\n\n"
        "Пожалуйста, укажите ваш город для определения часового пояса:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )
    logger.info(f"Started chat {chat_id}")

# /stop command
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.pop(chat_id)
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
    else:
        await update.message.reply_text("Вы не были подписаны.")

# City selection handler
async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    city = update.message.text.strip().lower()
    tz_map = {'москва':+3, 'киев':+3, 'тбилиси':+4, 'самара':+4}
    if city in tz_map:
        subscribers[chat_id] = tz_map[city]
        await update.message.reply_text(f"Город установлен: {city.capitalize()}. Рассылка активирована.")
        logger.info(f"Chat {chat_id} set timezone {tz_map[city]}")
    else:
        await update.message.reply_text("Город не распознан, попробуйте ещё раз.")

# Main entry point
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("setcity", set_city))
    # Schedule daily quotes at 9:00
    app.job_queue.run_daily(send_quote, time=time(hour=9, minute=0))
    # Schedule weekly reflections on Sunday at 12:00
    app.job_queue.run_daily(send_reflection, time=time(hour=12, minute=0), days=(6,))
    # Run bot
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
