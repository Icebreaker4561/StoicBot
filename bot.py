import logging
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from stoic_quotes_100 import QUOTES
import os

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Переменные
TOKEN = os.getenv("BOT_TOKEN")  # Берём токен из переменных окружения
subscribers = set()
scheduler = AsyncIOScheduler()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers.add(chat_id)
    await context.bot.send_message(
        chat_id=chat_id,
        text="✅ Вы подписаны на стоические цитаты, которые будут приходить каждую минуту."
    )
    logger.info(f"Новый подписчик: {chat_id}")

# Рассылка цитат
async def send_quote_to_all(context: ContextTypes.DEFAULT_TYPE):
    quote = random.choice(QUOTES)
    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id=chat_id, text=quote, parse_mode='HTML')
            logger.info(f"Цитата успешно отправлена в чат {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки цитаты в чат {chat_id}: {e}")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрируем команду
    app.add_handler(CommandHandler("start", start))

    # Планировщик рассылает цитату каждую минуту
    scheduler.add_job(send_quote_to_all, trigger="interval", minutes=1, args=[app])
    scheduler.start()

    logger.info("Бот запущен...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())import logging
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from stoic_quotes_100 import QUOTES
import os

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Переменные
TOKEN = os.getenv("BOT_TOKEN")  # Берём токен из переменных окружения
subscribers = set()
scheduler = AsyncIOScheduler()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers.add(chat_id)
    await context.bot.send_message(
        chat_id=chat_id,
        text="✅ Вы подписаны на стоические цитаты, которые будут приходить каждую минуту."
    )
    logger.info(f"Новый подписчик: {chat_id}")

# Рассылка цитат
async def send_quote_to_all(context: ContextTypes.DEFAULT_TYPE):
    quote = random.choice(QUOTES)
    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id=chat_id, text=quote, parse_mode='HTML')
            logger.info(f"Цитата успешно отправлена в чат {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки цитаты в чат {chat_id}: {e}")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрируем команду
    app.add_handler(CommandHandler("start", start))

    # Планировщик рассылает цитату каждую минуту
    scheduler.add_job(send_quote_to_all, trigger="interval", minutes=1, args=[app])
    scheduler.start()

    logger.info("Бот запущен...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())