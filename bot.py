import os
import logging
import random
from datetime import time
from telegram import ReplyKeyboardMarkup, Update
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
token = os.getenv("BOT_TOKEN")

# Subscribers storage: chat_id -> city
subscribers = {}

# --- Scheduled jobs ---
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in subscribers:
        quote = random.choice(QUOTES)
        try:
            await context.bot.send_message(chat_id, quote, parse_mode="HTML")
            logger.info(f"Quote sent to {chat_id}")
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
            await context.bot.send_message(chat_id, REFLECTION_TEXT, parse_mode="HTML")
            logger.info(f"Reflection sent to {chat_id}")
        except Exception as e:
            logger.error(f"Error sending reflection to {chat_id}: {e}")

# --- Command handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ask to choose city\    
    cities = ["Лермонтов", "Батуми", "Дюссельдорф", "Киев", "Барселона", "Лиссабон"]
    keyboard = [[c] for c in cities]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Пожалуйста, выберите ближайший к вам город из списка ниже, чтобы установить часовой пояс 👇",
        reply_markup=markup
    )
    logger.info(f"Prompted city selection for {update.effective_chat.id}")

async def setcity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text.strip()
    valid = ["Лермонтов", "Батуми", "Дюссельдорф", "Киев", "Барселона", "Лиссабон"]
    if city not in valid:
        await update.message.reply_text("Город не распознан, попробуйте ещё раз.")
        return
    chat_id = update.effective_chat.id
    subscribers[chat_id] = city
    await update.message.reply_text(
        "✅ Готово!\n"
        f"Теперь Вы будете получать одну мысль от стоиков каждое утро в 9:00 по времени города {city}.\n\n"
        "🔔⚠️ Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения."
    )
    logger.info(f"Subscribed {chat_id} for city {city}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.pop(chat_id)
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
        logger.info(f"Unsubscribed {chat_id}")
    else:
        await update.message.reply_text("Вы не были подписаны.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - подписаться и выбрать город\n"
        "/stop - отписаться от рассылки\n"
        "/setcity - изменить город/часовой пояс\n"
        "/share - поделиться ботом\n"
        "/help - показать это сообщение"
    )
    logger.info(f"Help requested by {update.effective_chat.id}")

async def share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Спасибо, что решили поделиться этим ботом 🙏 :)"
        "\nПросто перешлите это сообщение другу 👇"
    )
    await update.message.reply_text(
        "Привет! 👋 Хочу рекомендовать тебе классного бота. "
        "Он ежедневно присылает одну стоическую мысль. "
        "Мне очень понравилось: https://t.me/StoicTalesBot?start"
    )
    logger.info(f"Share messages sent to {update.effective_chat.id}")

# --- Main application setup ---
def main():
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setcity", setcity))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("share", share))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, setcity))

    # Schedule jobs
    app.job_queue.run_daily(send_quote, time=time(hour=9, minute=0), days=None)
    app.job_queue.run_daily(send_reflection, time=time(hour=12, minute=0), days=[6])

    logger.info("Scheduler starting...")
    app.run_polling()

if __name__ == '__main__':
    main()