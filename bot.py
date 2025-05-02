import os
import logging
import random
from datetime import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
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

# In-memory storage of subscribers: chat_id -> city
subscribers: dict[int, str] = {}

# Supported cities for timezone context
CITIES = [
    'Лермонтов', 'Батуми', 'Дюссельдорф',
    'Киев', 'Барселона', 'Лиссабон',
]

# Send a random stoic quote to all subscribers
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in subscribers.keys():
        quote = random.choice(QUOTES)
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=quote,
                parse_mode='HTML',
            )
            logger.info(f"Sent quote to {chat_id}")
        except Exception as e:
            logger.error(f"Failed sending quote to {chat_id}: {e}")

# Weekly reflection questions
REFLECTION_TEXT = (
    "🧘‍♂️ <b>Стоическая неделя. Время для размышлений.</b>\n"
    "<i>Эти вопросы не для галочки. Найди несколько минут тишины...</i>\n\n"
    "1️⃣ В каких ситуациях я позволил эмоциям взять верх над разумом,\n"  
    "   и как мог бы отреагировать более мудро, мужественно, справедливо и умеренно?\n"
    "2️⃣ Какие мои действия действительно соответствовали стоическим ценностям,\n"
    "   а какие шли вразрез с ними?\n"
    "3️⃣ Что из того, что я считал важным на этой неделе, действительно будет иметь значние через год?\n"
    "4️⃣ Какие возможности послужить другим людям я упустил на этой неделе?\n"
    "5️⃣ Какие препятствия и трудности этой недели я смог превратить в возможности для роста,\n    а какие уроки упустил?"
)

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in subscribers.keys():
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=REFLECTION_TEXT,
                parse_mode='HTML',
            )
            logger.info(f"Sent reflection to {chat_id}")
        except Exception as e:
            logger.error(f"Failed sending reflection to {chat_id}: {e}")

# /start or /setcity: prompt for city selection
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[city] for city in CITIES]
    markup = ReplyKeyboardMarkup(
        keyboard,
        one_time_keyboard=True,
        resize_keyboard=True,
    )
    await update.message.reply_text(
        "Пожалуйста, выберите ближайший к вам город из списка ниже, чтобы установить часовой пояс 👇",
        reply_markup=markup,
    )
    logger.info(f"Prompted city selection for {update.effective_chat.id}")

# Handle user city choice and subscribe
async def setcity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    city = update.message.text.strip()
    if city not in CITIES:
        await update.message.reply_text("Город не распознан, попробуйте ещё раз.")
        return
    subscribers[chat_id] = city
    await update.message.reply_text(
        "✅ Готово!\n"
        f"Теперь Вы будете получать одну мысль от стоиков каждое утро в 9:00 по времени города "
        f"<b>{city}</b>.\n\n"
        "🔔⚠️ Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения.",
        parse_mode='HTML',
    )
    logger.info(f"Subscribed {chat_id} with city {city}")

# /stop: unsubscribe from quotes and reflections
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.pop(chat_id)
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
        logger.info(f"Unsubscribed {chat_id}")
    else:
        await update.message.reply_text("Вы не были подписаны.")

# /help: usage instructions
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - подписаться и выбрать город\n"
        "/setcity - изменить город позже\n"
        "/stop - отписаться от рассылки\n"
        "/share - поделиться ботом\n"
        "/help - показать эту справку"
    )
    logger.info(f"Help sent to {update.effective_chat.id}")

# /share: send sharing instructions
async def share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Спасибо, что решили поделиться этим ботом 🙏 :)\n"
        "Просто перешлите это сообщение другу 👇"
    )
    await update.message.reply_text(
        "Привет! 👋 Хочу рекомендовать тебе классного бота. "
        "Он ежедневно присылает одну стоическую мысль. "
        "Мне очень понравилось: https://t.me/StoicTalesBot?start"
    )
    logger.info(f"Share info sent to {update.effective_chat.id}")

# Main entrypoint
def main():
    app = ApplicationBuilder().token(token).build()

    # Command & message handlers
    app.add_handler(CommandHandler(["start", "setcity"], start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, setcity))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("share", share))

    # Schedule jobs: daily quotes at 9:00 every day, reflection Sundays at 12:00
    jobq = app.job_queue
    jobq.run_daily(send_quote, time=time(hour=9, minute=0), days=tuple(range(7)))
    jobq.run_daily(send_reflection, time=time(hour=12, minute=0), days=(6,))  # Sunday=6

    app.run_polling()

if __name__ == "__main__":
    main()
