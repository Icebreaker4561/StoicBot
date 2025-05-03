import os
import logging
import random
import sqlite3
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

# Database setup
DB_PATH = os.getenv('DB_PATH', '/data/subscribers.db')
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS subs (chat_id INTEGER PRIMARY KEY, city TEXT)")
conn.commit()

# Send a random quote
def send_quote(context: CallbackContext):
    now = datetime.now()
    cursor.execute("SELECT chat_id, city FROM subs")
    rows = cursor.fetchall()
    for chat_id, city in rows:
        quote = random.choice(QUOTES)
        try:
            logger.info(f"Sending quote to {chat_id} ({city}) at {now}")
            context.bot.send_message(chat_id, quote, parse_mode='HTML')
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

def send_reflection(context: CallbackContext):
    now = datetime.now()
    cursor.execute("SELECT chat_id FROM subs")
    rows = cursor.fetchall()
    for (chat_id,) in rows:
        try:
            logger.info(f"Sending reflection to {chat_id} at {now}")
            context.bot.send_message(chat_id, REFLECTION_TEXT, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Error sending reflection to {chat_id}: {e}")

# /start command: ask user to pick city
def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cities = ['Лермонтов', 'Батуми', 'Дюссельдорф', 'Киев', 'Барселона', 'Лиссабон']
    keyboard = [[c] for c in cities]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(
        "Выберите город для расчёта времени рассылок:",
        reply_markup=reply_markup
    )
    logger.info(f"Prompted city selection for {chat_id}")

# Handle city selection

def setcity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    city = update.message.text.strip()
    supported = ['Лермонтов', 'Батуми', 'Дюссельдорф', 'Киев', 'Барселона', 'Лиссабон']
    if city not in supported:
        update.message.reply_text("Город не распознан, попробуйте ещё раз.")
        return
    cursor.execute("REPLACE INTO subs (chat_id, city) VALUES (?, ?)", (chat_id, city))
    conn.commit()
    update.message.reply_text(
        "✅ Готово!\n"
        "Теперь Вы будете получать одну мысль от стоиков каждое утро в 13:30 по времени города.\n\n"
        "🔔 Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения."
    )
    logger.info(f"Subscribed {chat_id} for city {city}")

# /stop command: unsubscribe
def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cursor.execute("DELETE FROM subs WHERE chat_id = ?", (chat_id,))
    conn.commit()
    update.message.reply_text("❌ Вы отписаны от рассылки.")
    logger.info(f"Unsubscribed {chat_id}")

# /share command
def share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.reply_text(
        "Спасибо, что решили поделиться этим ботом 🙏 :)\n"
        "Просто перешлите это сообщение другу 👇"
    )
    update.message.reply_text(
        "Привет! 👋 Хочу рекомендовать тебе классного бота. "
        "Он ежедневно присылает одну стоическую мысль. "
        "Мне очень понравилось: https://t.me/StoicTalesBot?start"
    )
    logger.info(f"Share messages sent to {update.effective_chat.id}")

# /help command
def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.reply_text(
        "/start - подписаться и выбрать город\n"
        "/stop - отписаться от рассылки\n"
        "/share - поделиться ботом\n"
        "/help - показать это сообщение"
    )
    logger.info(f"Help requested by {update.effective_chat.id}")

# Main function
def main():
    logger.info("Запуск приложения бота…")
    app = ApplicationBuilder().token(os.getenv('BOT_TOKEN')).build()
    
    # Register handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, setcity))
    app.add_handler(CommandHandler('stop', stop))
    app.add_handler(CommandHandler('share', share))
    app.add_handler(CommandHandler('help', help_cmd))

    # Schedule jobs
    logger.info("Регистрируем задачи планировщика: ежедневная цитата и еженедельная рефлексия")
    app.job_queue.run_daily(send_quote, time=time(hour=13, minute=30))
    app.job_queue.run_daily(send_reflection, time=time(hour=12, minute=0), days=(6,))

    app.run_polling()

if __name__ == '__main__':
    main()