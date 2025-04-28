import logging
import random
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from stoic_quotes_100 import QUOTES

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Переменные
TOKEN = os.getenv("BOT_TOKEN")
subscribers = set()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers.add(chat_id)
    await update.message.reply_text(
        "✅ Вы подписаны на стоические цитаты, которые будут приходить каждую минуту."
    )
    logger.info(f"Новый подписчик: {chat_id}")

# Отправка цитат
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    if subscribers:
        quote = random.choice(QUOTES)
        for chat_id in subscribers:
            try:
                await context.bot.send_message(chat_id=chat_id, text=quote, parse_mode='HTML')
                logger.info(f"Цитата отправлена в чат {chat_id}: {quote}")
            except Exception as e:
                logger.error(f"Ошибка отправки цитаты в чат {chat_id}: {e}")

# Главная функция
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # Периодическая задача через встроенный планировщик Telegram бота
    app.job_queue.run_repeating(send_quote, interval=60, first=10)

    logger.info("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()