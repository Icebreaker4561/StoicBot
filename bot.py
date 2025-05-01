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
    filters,
)
from telegram.ext import CallbackContext
from telegram.ext import JobQueue
from stoic_quotes_100 import QUOTES

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Переменные
TOKEN = os.getenv("BOT_TOKEN")
subscribers = set()

# Цитаты
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    if subscribers:
        quote = random.choice(QUOTES)
        for chat_id in subscribers:
            try:
                await context.bot.send_message(chat_id=chat_id, text=quote, parse_mode='HTML')
                logger.info(f"Цитата отправлена в {chat_id}")
            except Exception as e:
                logger.error(f"Ошибка при отправке цитаты: {e}")

# Рефлексия
REFLECTION_TEXT = (
    "<b>🧠 Недельная рефлексия</b>\n"
    "<i>— В каких ситуациях я позволил эмоциям взять верх, и как я мог бы отреагировать более мудро?</i>\n"
    "<i>— Какие мои действия соответствовали стоическим ценностям, а какие ему противоречили?</i>\n"
    "<i>— Что из этой недели будет иметь значение через год?</i>\n"
    "<i>— Когда я упустил шанс помочь другим?</i>\n"
    "<i>— Какие препятствия стали моим ростом?</i>"
)

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    if subscribers:
        for chat_id in subscribers:
            try:
                await context.bot.send_message(chat_id=chat_id, text=REFLECTION_TEXT, parse_mode='HTML')
                logger.info(f"Рефлексия отправлена в {chat_id}")
            except Exception as e:
                logger.error(f"Ошибка рефлексии: {e}")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers.add(chat_id)
    await update.message.reply_text(
        "✅ Вы подписаны на цитаты и еженедельную рефлексию. Вы будете получать сообщения каждую минуту."
    )
    logger.info(f"Подписался: {chat_id}")

# /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        await update.message.reply_text("❌ Вы отписаны.")
    else:
        await update.message.reply_text("Этот чат не был подписан.")

# main
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))

    # Цитаты каждую минуту
    app.job_queue.run_repeating(send_quote, interval=30, first=5)
    # Рефлексия каждую минуту
    app.job_queue.run_repeating(send_reflection, interval=30, first=15)

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
