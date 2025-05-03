import os
import logging
import random
from datetime import datetime, time
import pytz
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

# Subscribers storage: chat_id -> {'city': city_name, 'tz': timezone}
subscribers = {}

# Send a random quote
async def send_quote(context: CallbackContext):
    logger.info("Running send_quote job")
    for chat_id, info in subscribers.items():
        tz = info.get('tz') or pytz.utc
        quote = random.choice(QUOTES)
        try:
            logger.info(f"Sending quote to {chat_id} at tz {tz}")
            await context.bot.send_message(chat_id, quote, parse_mode='HTML')
            logger.info(f"Quote sent to {chat_id}")
        except Exception as e:
            logger.error(f"Error sending quote to {chat_id}: {e}")

# Weekly reflection message
REFLECTION_TEXT = (
    "🧘‍♂️ <b>Стоическая неделя</b>\n"
    "<i>Эти вопросы не для галочки. Найди несколько минут тишины, чтобы честно взглянуть на прожитую неделю.</i>\n\n"
    "1️⃣ В каких ситуациях на этой неделе я позволил эмоциям взять верх над разумом, и как мог бы отреагировать более мудро, мужественно, справедливо и умеренно?\n"
    "2️⃣ Какие мои действия действительно соответствовали стоическим ценностям и принципам, а какие шли вразрез с ними?\n"
    "3️⃣ Что из того, что я считал важным на этой неделе, действительно будет иметь значение через год?\n"
    "4️⃣ Какие возможности послужить другим людям я упустил на этой неделе?\n"
    "5️⃣ Какие препятствия и трудности этой недели я смог превратить в возможности для роста, а какие уроки упустил?"
)

async def send_reflection(context: CallbackContext):
    logger.info("Running send_reflection job")
    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id, REFLECTION_TEXT, parse_mode='HTML')
            logger.info(f"Reflection sent to {chat_id}")
        except Exception as e:
            logger.error(f"Error sending reflection to {chat_id}: {e}")

# /start command: ask user to pick city/timezone
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.info(f"Received /start from {chat_id}")
    cities = ['Лермонтов', 'Батуми', 'Дюссельдорф', 'Киев', 'Барселона', 'Лиссабон']
    keyboard = [[c] for c in cities]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Пожалуйста, выберите ближайший к вам город из списка ниже, чтобы установить часовой пояс 👇",
        reply_markup=reply_markup
    )
    logger.info(f"Prompted city selection for {chat_id}")

# Handle city selection and subscribe
async def setcity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    city = update.message.text.strip()
    logger.info(f"User {chat_id} selected city {city}")
    tz_map = {
        'Лермонтов': 'Europe/Moscow',
        'Батуми': 'Asia/Tbilisi',
        'Дюссельдорф': 'Europe/Berlin',
        'Киев': 'Europe/Kiev',
        'Барселона': 'Europe/Madrid',
        'Лиссабон': 'Europe/Lisbon',
    }
    if city not in tz_map:
        await update.message.reply_text("Город не распознан, попробуйте ещё раз.")
        return
    tz_str = tz_map[city]
    tz = pytz.timezone(tz_str)
    subscribers[chat_id] = {'city': city, 'tz': tz}
    await update.message.reply_text(
        f"✅ Готово!\n"
        f"Теперь Вы будете получать одну мысль от стоиков каждое утро в 12:30 по времени города ({city}).\n\n"
        "🔔 Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения."
    )
    logger.info(f"Subscribed {chat_id}: city={city}, tz={tz_str}")

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

async def main():
    logger.info("Starting bot application")
    app = ApplicationBuilder().token(TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, setcity))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("share", share))

    logger.info("Registering job queue: daily quote and weekly reflection")
    # Schedule daily quote at 12:30 user tz
    app.job_queue.run_daily(
        send_quote,
        time=time(hour=12, minute=30),
        days=(0,1,2,3,4,5,6),
        tzinfo=lambda name: subscribers.get(name).get('tz') if name in subscribers else pytz.utc
    )
    # Schedule weekly reflection Sunday (6) at 12:00
    app.job_queue.run_daily(
        send_reflection,
        time=time(hour=12, minute=0),
        days=(6,)
    )

    logger.info("Starting polling")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())