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
    CallbackContext,
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

# Subscribers storage: chat_id -> selected city (placeholder for timezone)
subscribers = {}

# Send a random quote to all subscribers
def send_random_quote(context: CallbackContext) -> None:
    for chat_id in list(subscribers.keys()):
        quote = random.choice(QUOTES)
        try:
            context.bot.send_message(chat_id=chat_id, text=quote, parse_mode='HTML')
            logger.info(f"Quote sent to {chat_id}")
        except Exception as e:
            logger.error(f"Error sending quote to {chat_id}: {e}")

# Weekly reflection message
REFLECTION_TEXT = (
    "🧘‍♂️ <b>Стоическая неделя</b>\n"
    "<i>Эти вопросы не для галочки. Найди несколько минут тишины...</i>\n\n"
    "1️⃣ В каких ситуациях я позволил эмоциям взять верх над разумом?\n"
    "2️⃣ Какие мои действия соответствовали стоическим ценностям, а какие — нет?\n"
    "3️⃣ Что из того, что я считал важным, действительно будет иметь значение через год?\n"
    "4️⃣ Какие возможности послужить другим я упустил?\n"
    "5️⃣ Какие трудности я смог превратить в возможности для роста?"
)

def send_weekly_reflection(context: CallbackContext) -> None:
    for chat_id in list(subscribers.keys()):
        try:
            context.bot.send_message(chat_id=chat_id, text=REFLECTION_TEXT, parse_mode='HTML')
            logger.info(f"Reflection sent to {chat_id}")
        except Exception as e:
            logger.error(f"Error sending reflection to {chat_id}: {e}")

# /start command: ask user to pick city for timezone
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    cities = ['Лермонтов', 'Батуми', 'Дюссельдорф', 'Киев', 'Барселона', 'Лиссабон']
    keyboard = [[city] for city in cities]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "Пожалуйста, выберите ближайший к вам город из списка ниже, чтобы установить часовой пояс 👇",
        reply_markup=reply_markup
    )
    logger.info(f"Prompted city selection for {chat_id}")

# Handle city selection and subscribe user
async def setcity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    city = update.message.text.strip()
    valid = ['Лермонтов', 'Батуми', 'Дюссельдорф', 'Киев', 'Барселона', 'Лиссабон']
    if city not in valid:
        await update.message.reply_text("Город не распознан, попробуйте ещё раз.")
        return

    subscribers[chat_id] = city
    await update.message.reply_text(
        "✅ Готово!\n"
        f"Теперь Вы будете получать одну мысль от стоиков каждое утро в 12:15 по времени города ({city}).\n\n"
        "🔔 Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения."
    )
    logger.info(f"Subscribed {chat_id} with city {city}")

# /stop command: unsubscribe user
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.pop(chat_id)
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
        logger.info(f"Unsubscribed {chat_id}")
    else:
        await update.message.reply_text("Вы не были подписаны.")

# /help command: show usage
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "/start - подписаться и выбрать город\n"
        "/stop - отписаться от рассылки\n"
        "/setcity - изменить город/часовой пояс\n"
        "/share - поделиться ботом\n"
        "/help - показать это сообщение"
    )
    logger.info(f"Help requested by {update.effective_chat.id}")

# /share command: send invite link
async def share(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Спасибо, что решили поделиться этим ботом 🙏 :)\n"
        "Просто перешлите это сообщение другу 👇"
    )
    await update.message.reply_text(
        "Привет! 👋 Хочу рекомендовать тебе классного бота. "
        "Он ежедневно присылает одну стоическую мысль. "
        "Мне очень понравилось: https://t.me/StoicTalesBot?start"
    )
    logger.info(f"Share messages sent to {update.effective_chat.id}")

# Main function to set up and run the bot
async def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setcity", setcity))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("share", share))

    # Catch-all for city selection messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, setcity))

    # Schedule jobs: daily quote at 12:15, weekly reflection on Sunday (weekday=6) at 12:00
    application.job_queue.run_daily(send_random_quote, time=time(hour=12, minute=15))
    application.job_queue.run_daily(send_weekly_reflection, time=time(hour=12, minute=0), days=(6,))

    # Start the bot
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())