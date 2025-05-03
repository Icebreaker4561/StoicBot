import os
import logging
import random
import sqlite3
from datetime import datetime, time
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

# Database helper
DB_PATH = "/data/subscribers.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS subs (chat_id INTEGER PRIMARY KEY, city TEXT)"
    )
    conn.commit()
    conn.close()

async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for chat_id, city in cur.execute("SELECT chat_id, city FROM subs"):  # noqa
        quote = random.choice(QUOTES)
        try:
            logger.info(f"Sending quote to {chat_id} ({city})")
            await context.bot.send_message(chat_id, quote)
        except Exception as e:
            logger.error(f"Error sending quote to {chat_id}: {e}")
    conn.close()

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    # ... weekly reflection logic here
    pass

# /start command: ask user to pick city
def build_city_keyboard():
    cities = ['Лермонтов', 'Батуми', 'Дюссельдорф', 'Киев', 'Барселона', 'Лиссабон']
    return ReplyKeyboardMarkup(
        [[c] for c in cities], one_time_keyboard=True, resize_keyboard=True
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/start invoked by {update.effective_chat.id}")
    await update.message.reply_text(
        "Пожалуйста, выберите ближайший к вам город из списка ниже, чтобы установить часовой пояс 👇",
        reply_markup=build_city_keyboard()
    )

# Handle city selection and subscribe
async def setcity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    city = update.message.text.strip()
    if city not in ['Лермонтов', 'Батуми', 'Дюссельдорф', 'Киев', 'Барселона', 'Лиссабон']:
        await update.message.reply_text("Город не распознан, пожалуйста, выберите из списка.")
        return
    logger.info(f"Subscribing {chat_id} for city {city}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "REPLACE INTO subs (chat_id, city) VALUES (?, ?)", (chat_id, city)
    )
    conn.commit()
    conn.close()
    await update.message.reply_text(
        "✅ Готово!\n"
        f"Теперь Вы будете получать одну мысль от стоиков каждое утро в 9:00 по времени города {city}.\n\n"
        "🔔⚠️ Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения."
    )

# Other commands (/stop, /help, /share) defined similarly...
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM subs WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text("❌ Вы отписаны от рассылки.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — подписаться и выбрать город\n"
        "/stop — отписаться\n"
        "/help — помощь\n"
        "/share — поделиться ботом"
    )

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

# Main
async def main():
    logger.info("Запуск приложения бота…")
    init_db()
    token = os.getenv('BOT_TOKEN')
    app = ApplicationBuilder().token(token).build()

    # Handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.Regex('^(Лермонтов|Батуми|Дюссельдорф|Киев|Барселона|Лиссабон)$'), setcity))
    app.add_handler(CommandHandler('stop', stop))
    app.add_handler(CommandHandler('help', help_cmd))
    app.add_handler(CommandHandler('share', share))

    # Scheduler
    logger.info("Регистрируем задачи планировщика: ежедневная цитата и еженедельная рефлексия")
    app.job_queue.run_daily(send_quote, time=time(hour=9, minute=0))
    app.job_queue.run_daily(send_reflection, time=time(hour=12, minute=0), days='sat')

    await app.run_polling()

if __name__ == '__main__':
    import asynаcio
    asyncio.run(main())