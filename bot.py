import os
import logging
import random
import asyncio
from datetime import time
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from stoic_quotes_100 import QUOTES

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Bot token from environment (set BOT_TOKEN_DEV or BOT_TOKEN)
TOKEN = os.getenv("BOT_TOKEN_DEV") or os.getenv("BOT_TOKEN")

# In-memory subscribers: chat_id -> city
subscribers = {}

async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, city in subscribers.items():
        quote = random.choice(QUOTES)
        try:
            await context.bot.send_message(chat_id, quote, parse_mode='HTML')
            logger.info(f"Sent quote to {chat_id} for city {city}")
        except Exception as e:
            logger.error(f"Error sending quote to {chat_id}: {e}")

REFLECTION_TEXT = (
    "🧘‍♂️ <b>Стоическая неделя</b>\n"
    "<i>Эти вопросы не для галочки. Найди несколько минут тишины...</i>\n\n"
    "1️⃣ В каких ситуациях я позволил эмоциям взять верх над разумом?\n"
    "2️⃣ Какие мои действия соответствовали стоическим ценностям, а какие — нет?\n"
    "3️⃣ Что из того, что я считал важным, действительно будет иметь значение через год?\n"
    "4️⃣ Какие возможности послужить другим я упустил?\n"
    "5️⃣ Какие трудности я смог превратить в возможности для роста?"
)

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id, REFLECTION_TEXT, parse_mode='HTML')
            logger.info(f"Sent reflection to {chat_id}")
        except Exception as e:
            logger.error(f"Error sending reflection to {chat_id}: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cities = ['Лермонтов', 'Батуми', 'Дюссельдорф', 'Киев', 'Барселона', 'Лиссабон']
    keyboard = [[c] for c in cities]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Пожалуйста, выберите ближайший к вам город из списка ниже, чтобы установить часовой пояс 👇",
        reply_markup=reply_markup
    )
    logger.info(f"Prompted city selection for {chat_id}")

async def setcity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    city = update.message.text.strip()
    valid = ['Лермонтов', 'Батуми', 'Дюссельдорф', 'Киев', 'Барселона', 'Лиссабон']
    if city not in valid:
        await update.message.reply_text("Город не распознан, попробуйте ещё раз.")
        return
    subscribers[chat_id] = city
    await update.message.reply_text(
        "✅ Готово!\n"
        f"Теперь Вы будете получать одну мысль от стоиков каждое утро в 13:05 по времени города {city}.\n\n"
        "🔔⚠️ Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения.",
        reply_markup=ReplyKeyboardRemove()
    )
    logger.info(f"Subscribed {chat_id} with city {city}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if subscribers.pop(chat_id, None):
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
        logger.info(f"Unsubscribed {chat_id}")
    else:
        await update.message.reply_text("Вы не были подписаны.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - подписаться и выбрать город\n"
        "/stop - отписаться от рассылки\n"
        "/share - поделиться ботом\n"
        "/help - показать это сообщение"
    )

async def share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Спасибо, что решили поделиться этим ботом 🙏 :)\nПерешлите это сообщение другу 👇"
    )
    await update.message.reply_text(
        "Привет! 👋 Хочу рекомендовать тебе классного бота. "
        "Он ежедневно присылает одну стоическую мысль. "
        "Мне очень понравилось: https://t.me/StoicTalesBot?start"
    )
    logger.info(f"Share initiated by {update.effective_chat.id}")

async def main():
    logger.info("Запуск приложения бота…")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("share", share))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, setcity))

    # Schedule daily quote at 13:05 and weekly reflection Saturday 12:00
    logger.info("Регистрируем задачи планировщика: ежедневная цитата и еженедельная рефлексия")
    app.job_queue.run_daily(send_quote, time=time(hour=13, minute=5))
    app.job_queue.run_daily(send_reflection, time=time(hour=12, minute=0), days=(5,))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.idle()

if __name__ == '__main__':
    asyncio.run(main())