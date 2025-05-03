import os
import logging
import random
from datetime import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from stoic_quotes_100 import QUOTES

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Bot token from environment
TOKEN = os.getenv("BOT_TOKEN")

# In-memory subscribers: chat_id -> city
subscribers = {}

# Send a random quote
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, city in subscribers.items():
        quote = random.choice(QUOTES)
        try:
            await context.bot.send_message(
                chat_id,
                f"<b>Стоическая мысль:</b>\n{quote}",
                parse_mode="HTML",
            )
            logger.info(f"Sent quote to {chat_id} ({city})")
        except Exception as e:
            logger.error(f"Error sending quote to {chat_id}: {e}")

# Weekly reflection text
REFLECTION_TEXT = (
    "🧘‍♂️ <b>Стоическая неделя</b>\n"
    "Эти вопросы не для галочки. Найдите 5–10 минут для честной рефлексии:\n"
    "1️⃣ В каких ситуациях я позволил эмоциям взять верх над разумом?\n"
    "2️⃣ Какие мои действия соответствовали стоическим ценностям, а какие нет?\n"
    "3️⃣ Что из того, что я считал важным, будет важно через год?\n"
    "4️⃣ Какие возможности помочь другим я упустил?\n"
    "5️⃣ Какие трудности я смог превратить в рост, а чему еще нужно научиться?"
)

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, city in subscribers.items():
        try:
            await context.bot.send_message(
                chat_id,
                REFLECTION_TEXT,
                parse_mode="HTML",
            )
            logger.info(f"Sent reflection to {chat_id} ({city})")
        except Exception as e:
            logger.error(f"Error sending reflection to {chat_id}: {e}")

# /start: ask to choose city
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cities = ['Лермонтов','Батуми','Дюссельдорф','Киев','Барселона','Лиссабон']
    keyboard = [[c] for c in cities]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Пожалуйста, выберите ближайший к вам город из списка ниже, чтобы установить часовой пояс 👇",
        reply_markup=reply_markup,
    )
    logger.info(f"Prompted city selection for {chat_id}")

# /setcity or city name handler
def is_city(text: str):
    return text in ['Лермонтов','Батуми','Дюссельдорф','Киев','Барселона','Лиссабон']

async def setcity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    city = update.message.text.strip()
    if not is_city(city):
        return
    subscribers[chat_id] = city
    await update.message.reply_text(
        "✅ Готово!\n"
        f"Теперь вы будете получать одну мысль от стоиков каждое утро в 11:25 по времени города {city}.\n\n"
        "🔔⚠️ Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения."
    )
    logger.info(f"Subscribed {chat_id} for city {city}")

# /stop: unsubscribe
def unregister(chat_id: int):
    return subscribers.pop(chat_id, None)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if unregister(chat_id):
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
        logger.info(f"Unsubscribed {chat_id}")
    else:
        await update.message.reply_text("Вы не были подписаны.")

# /help
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — подписаться и выбрать город\n"
        "/stop — отписаться\n"
        "/help — помощь\n"
        "/share — поделиться ботом"
    )

# /share
async def share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Спасибо, что решили поделиться этим ботом 🙏 :)\n"  
        "Просто перешлите это сообщение другу 👇"
    )
    await update.message.reply_text(
        "Привет! 👋 Хочу рекомендовать тебе классного бота. "
        "Он ежедневно присылает одну стоическую мысль. "
        "Мне очень понравилось: https://t.me/StoicTalesBot_dev_bot?start"
    )
    logger.info(f"Share prompt sent to {update.effective_chat.id}")

# Main
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, setcity))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("share", share))
    # Schedule jobs: daily at 11:05 and weekly Sunday at 12:00
    app.job_queue.run_daily(send_quote, time=time(hour=11, minute=25), days=(0,1,2,3,4,5,6))
    app.job_queue.run_daily(send_reflection, time=time(hour=12, minute=0), days=(6,))
    app.run_polling()
