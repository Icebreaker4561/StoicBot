import logging
from pathlib import Path
import os
import sqlite3
from zoneinfo import ZoneInfo
from datetime import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes
)

# --- Setup logging ---
# Ensure /data is present for disk-mounted storage
Path("/data").mkdir(parents=True, exist_ok=True)

LOG_FILE = "/data/bot.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ],
)
logger = logging.getLogger(__name__)

# --- Database setup ---
DB_PATH = "/data/subscribers.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS subs(
            chat_id INTEGER PRIMARY KEY,
            city TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

# Predefined cities and their time zones
CITIES = {
    "Батуми": "Asia/Tbilisi",
    "Москва": "Europe/Moscow",
    "Лермонтов": "Europe/Moscow",
    # ... add more as needed
}

# Sample quotes
QUOTES = [
    "Ты жалеешься, что всё в жизни происходит слишком быстро... — Сенека",
    "Умей владеть собой — это ключ к настоящей свободе. — Эпиктет",
    # ... пополняйте список
]

# --- Bot handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.info(f"/start от {chat_id}")
    # Build inline keyboard for city selection
    keyboard = [
        [InlineKeyboardButton(city, callback_data=city)]
        for city in CITIES
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Пожалуйста, выберите ближайший к вам город из списка ниже, чтобы установить часовой пояс 👇",
        reply_markup=reply_markup
    )

async def city_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    city = query.data
    chat_id = query.message.chat.id
    # Register in DB
    register_user(chat_id, city)
    # Schedule daily job
    tz = ZoneInfo(CITIES[city])
    schedule_quote(chat_id, tz)
    logger.info(f"{chat_id} подписан на город '{city}'")
    # Confirm to user
    await query.edit_message_text(
        f"✅ Готово! Теперь вы будете получать одну мысль от стоиков каждое утро в 09:00 по времени города ({city}).\n"
        "🔔⚠️ Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения."
    )

async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = int(job.name)
    logger.info(f"Попытка отправить цитату {chat_id}")
    quote = random.choice(QUOTES)
    try:
        await context.bot.send_message(chat_id, quote)
        logger.info(f"Цитата отправлена {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки цитаты {chat_id}: {e}")

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    # Weekly reflection on Saturday
    all_chats = get_all_subscribers()
    for chat_id, city in all_chats:
        logger.info(f"Отправка еженедельной рефлексии {chat_id}")
        await context.bot.send_message(chat_id, "Время для еженедельной рефлексии — как прошла неделя?")

# --- Scheduling and DB helpers ---
def register_user(chat_id: int, city: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "REPLACE INTO subs(chat_id, city) VALUES (?, ?)",
        (chat_id, city)
    )
    conn.commit()
    conn.close()

def get_all_subscribers():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT chat_id, city FROM subs")
    rows = c.fetchall()
    conn.close()
    return rows

# Each subscriber gets their own daily job named by chat_id

def schedule_quote(chat_id: int, tz: ZoneInfo):
    run_time = time(hour=9, minute=0, tzinfo=tz)
    context_app.job_queue.run_daily(
        send_quote,
        time=run_time,
        days=(0,1,2,3,4,5,6),
        name=str(chat_id)
    )
    logger.info(f"Scheduled quote для {chat_id} в {run_time}")

# --- Main application setup ---

async def main():
    init_db()
    token = os.getenv('TELEGRAM_TOKEN')
    app = Application.builder().token(token).build()
    global context_app
    context_app = app  # for scheduler helper

    # Handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(city_selected))

    # Scheduler jobs
    app.job_queue.run_daily(
        send_reflection,
        time=time(hour=12, minute=0),
        days=(6,)
    )
    logger.info("Scheduled daily quote at 09:00 and weekly reflection on Saturday at 12:00")

    # Start polling
    logger.info("Starting bot application")
    await app.run_polling()

if __name__ == '__main__':
    import asyncio, random
    asyncio.run(main())
