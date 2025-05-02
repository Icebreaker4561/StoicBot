import os
import logging
import random
import asyncio
from datetime import time
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
    format="%(asctime)s – %(name)s – %(levelname)s – %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Хранение подписчиков и их временных зон
subscribers = {}  # chat_id -> timezone string, пока не используется

# Отправка цитаты
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in subscribers.keys():
        quote = random.choice(QUOTES)
        try:
            await context.bot.send_message(chat_id, quote, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка при отправке цитаты {chat_id}: {e}")

# Отправка рефлексии
REFLECTION = (
    "🧘‍♂️ *Стоическая неделя*\n"
    "_Эти вопросы не для галочки. Найди несколько минут тишины._\n\n"
    "1️⃣ В каких ситуациях я позволил эмоциям взять верх над разумом?\n"
    "2️⃣ Какие мои действия соответствовали стоическим ценностям, а какие — нет?\n"
    "3️⃣ Что из того, что я считал важным, будет иметь значение через год?\n"
    "4️⃣ Какие возможности помочь другим я упустил?\n"
    "5️⃣ Какие трудности этой недели я смог превратить в рост?"
)

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in subscribers.keys():
        try:
            await context.bot.send_message(
                chat_id,
                REFLECTION,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке рефлексии {chat_id}: {e}")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers[chat_id] = None  # можем позже сохранять часовой пояс
    await update.message.reply_text(
        "✅ Готово!\n"
        "Теперь Вы будете получать одну мысль из стоицизма каждое утро в 9:00.\n\n"
        "🔔 Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения."
    )
    logger.info(f"Подписался: {chat_id}")

# /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.pop(chat_id, None)
        await update.message.reply_text("❌ Вы отписаны.")
        logger.info(f"Отписался: {chat_id}")
    else:
        await update.message.reply_text("Вы и так не были подписаны.")

# Главная точка входа
def main():
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))

    # Ежедневные цитаты в 09:00
    app.job_queue.run_daily(
        send_quote,
        time=time(hour=9, minute=0),
        days=(0,1,2,3,4,5,6),
    )
    # Еженедельная рефлексия в воскресенье в 12:00
    app.job_queue.run_daily(
        send_reflection,
        time=time(hour=12, minute=0),
        days=(6,),
    )

    # Для Render: используем .run(), а не .run_polling()
    app.run()

if __name__ == "__main__":
    main()