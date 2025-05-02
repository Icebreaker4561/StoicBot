import os
import logging
import random
from datetime import datetime, time
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

# Subscribers storage: chat_id -> city/Timezone placeholder
subscribers = {}

# Send a random quote
async def send_quote(context: CallbackContext):
    for chat_id in subscribers:
        quote = random.choice(QUOTES)
        try:
            await context.bot.send_message(chat_id, quote, parse_mode='HTML')
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

async def send_reflection(context: CallbackContext):
    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id, REFLECTION_TEXT, parse_mode='HTML')
            logger.info(f"Reflection sent to {chat_id}")
        except Exception as e:
            logger.error(f"Error sending reflection to {chat_id}: {e}")

# /start command: ask user to pick city
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cities = ['Лермонтов', 'Батуми', 'Дюссельдорф', 'Киев', 'Барселона', 'Лиссабон']
    keyboard = [[c] for c in cities]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
    f"✅ Готово!
"
    f"Теперь Вы будете получать одну мысль от стоиков каждое утро в 9:00 по времени города ({city}).

"
    "🔔⚠️ Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения."
)
    logger.info(f"Prompted city selection for {chat_id}")

# Handle city selection and subscribe
async def setcity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    city = update.message.text.strip()
    if city not in ['Лермонтов', 'Батуми', 'Дюссельдорф', 'Киев', 'Барселона', 'Лиссабон']:
        await update.message.reply_text("Город не распознан, попробуйте ещё раз.")
        return
    subscribers[chat_id] = city  # store city or timezone mapping later
    await update.message.reply_text(
        "✅ Готово!\n"
        "Теперь Вы будете получать одну мысль от стоиков каждое утро в 9:00.\n\n"
        "🔔 Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения."
    )
    logger.info(f"Subscribed {chat_id} for city {city}")

# /stop command: unsubscribe
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.pop(chat_id)
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
        logger.info(f"Unsubscribed {chat_id}")
    else:
        await update.message.reply_text("Вы не были подписаны.")

# /help command: show usage
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - подписаться и выбрать город\n"
        "/stop - отписаться от рассылки\n"
        "/setcity <город> - изменить город/часовой пояс\n"
        "/share - поделиться ботом\n"
        "/help - показать это сообщение"
    )
    logger.info(f"Help requested by {update.effective_chat.id}")

# /share command: send invite link
async def share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # First message with gratitude and forwarding instructions
    await update.message.reply_text(
        "Спасибо, что решили поделиться этим ботом 🙏 :)
"
        "Просто перешлите это сообщение другу 👇"
    )
    # Second message with recommendation link
    await update.message.reply_text(
        "Привет! 👋 Хочу рекомендовать тебе классного бота. "
        "Он ежедневно присылает одну стоическую мысль. "
        "Мне очень понравилось: https://t.me/StoicTalesBot?start"
    )
    logger.info(f"Share messages sent to {update.effective_chat.id}")

