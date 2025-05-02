import os
import logging
import random
from datetime import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from stoic_quotes_100 import QUOTES

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
TOKEN = os.getenv("BOT_TOKEN")

# In-memory storage
subscribers = {}

# Keyboard options
CITIES = ["Москва", "Киев", "Самара", "Тбилиси", "Рим", "Барселона", "Лондон"]

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[city] for city in CITIES]
    await update.message.reply_text(
        "Пожалуйста, выберите свой город:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )

async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    if city not in CITIES:
        await update.message.reply_text("Город не распознан, попробуйте ещё раз.")
        return
    chat_id = update.effective_chat.id
    subscribers[chat_id] = city
    text = (
        "✅ Готово!\n"
        "Теперь Вы будете получать одну мысль из стоицизма каждое утро в 9:00.\n\n"
        "🔔 Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения."
    )
    await update.message.reply_text(text)
    logger.info(f"Подписан {chat_id} в городе {city}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.pop(chat_id)
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
        logger.info(f"Отписан {chat_id}")
    else:
        await update.message.reply_text("Вы не были подписаны.")

async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in list(subscribers):
        quote = random.choice(QUOTES)
        try:
            await context.bot.send_message(chat_id=chat_id, text=quote, parse_mode='HTML')
            logger.info(f"Цитата отправлена {chat_id}")
        except Exception as e:
            logger.error(f"Не получилось отправить цитату {chat_id}: {e}")

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🧘‍♂️ Стоическая неделя. Время для размышлений.\n\n"
        "Эти вопросы не для галочки. Найдите пару минут тишины. Ответы не обязательны, но помогут вам расти.\n\n"
        "1️⃣ В каких ситуациях я позволил эмоциям взять верх над разумом, и как мог бы отреагировать более мудро, мужественно, справедливо и умеренно?\n"
        "2️⃣ Какие мои действия действительно соответствовали стоическим ценностям и принципам, а какие шли вразрез с ними?\n"
        "3️⃣ Что из того, что я считал важным на этой неделе, действительно будет иметь значение через год?\n"
        "4️⃣ Какие возможности послужить другим людям я упустил на этой неделе?\n"
        "5️⃣ Какие препятствия и трудности этой недели я смог превратить в возможности для роста, а какие уроки упустил?"
    )
    for chat_id in list(subscribers):
        try:
            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
            logger.info(f"Рефлексия отправлена {chat_id}")
        except Exception as e:
            logger.error(f"Не получилось отправить рефлексию {chat_id}: {e}")

# Main entrypoint
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_city))

    # Schedule: daily quotes at 9:00
    app.job_queue.run_daily(send_quote, time=time(hour=9, minute=0))
    # Schedule: weekly reflection Sunday at 12:00
    app.job_queue.run_daily(send_reflection, time=time(hour=12, minute=0), days=[6])

    app.run_polling()
