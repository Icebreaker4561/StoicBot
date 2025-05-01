import os
import logging
import random
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from stoic_quotes_100 import QUOTES
from datetime import datetime

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
    logger.info("🔁 Вызвана функция send_quote")
    if not subscribers:
        logger.info("Нет подписчиков для цитат")
        return
    quote = random.choice(QUOTES)
    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id=chat_id, text=quote, parse_mode='HTML')
            logger.info(f"✅ Цитата отправлена в чат {chat_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке цитаты в чат {chat_id}: {e}")

# Рефлексия
REFLECTION_TEXT = (
    "<b>🧠 Недельная рефлексия</b>\n"
    "<i>👉 В каких ситуациях я позволил эмоциям взять верх, и как я мог бы отреагировать более мудро?</i>\n"
    "<i>👉 Какие мои действия соответствовали стоическим ценностям, а какие ему противоречили?</i>\n"
    "<i>👉 Что из этой недели будет иметь значение через год?</i>\n"
    "<i>👉 Когда я упустил шанс помочь другим?</i>\n"
    "<i>👉 Какие препятствия стали моим ростом?</i>"
)

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    logger.info("🔁 Вызвана функция send_reflection")
    if not subscribers:
        logger.info("Нет подписчиков для рефлексии")
        return
    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id=chat_id, text=REFLECTION_TEXT, parse_mode='HTML')
            logger.info(f"✅ Рефлексия отправлена в чат {chat_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке рефлексии в чат {chat_id}: {e}")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers.add(chat_id)
    logger.info(f"📥 Новый подписчик: {chat_id}")
    await update.message.reply_text(
        "✅ Вы подписаны на stoic-цитаты и еженедельную рефлексию. Тестовый режим: каждые 30 секунд."
    )

# Команда /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        logger.info(f"📤 Подписчик удалён: {chat_id}")
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
    else:
        await update.message.reply_text("Вы не были подписаны.")

# Запуск
import asyncio
from telegram.ext import Application

async def main():
    logger.info("🚀 Запуск бота")
    app: Application = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))

    app.job_queue.run_repeating(send_quote, interval=30, first=5)
    app.job_queue.run_repeating(send_reflection, interval=30, first=15)

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    logger.info("✅ Бот успешно запущен")
    await asyncio.Event().wait()  # Бесконечный цикл

if __name__ == "__main__":
    asyncio.run(main())
