
import logging
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from apscheduler.schedulers.background import BackgroundScheduler
from stoic_quotes_100 import QUOTES
import random

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Получение переменных окружения
TOKEN = os.getenv("BOT_TOKEN")

# Хранилище пользователей
subscribers = set()

# Рассылка цитаты
async def send_quote_to_all(context: ContextTypes.DEFAULT_TYPE):
    if not subscribers:
        return
    quote = random.choice(QUOTES)
    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id=chat_id, text=quote, parse_mode="HTML")
            logging.info(f"Отправлена цитата пользователю {chat_id}: {quote}")
        except Exception as e:
            logging.error(f"Ошибка при отправке цитаты пользователю {chat_id}: {e}")

# Команда подписки
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers.add(chat_id)
    await update.message.reply_text("✅ Вы подписаны на стоические цитаты, которые будут приходить каждую минуту.")

# Команда отписки
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers.discard(chat_id)
    await update.message.reply_text("❌ Вы отписались от рассылки стоических цитат.")

# Инициализация и запуск бота
if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()

    # Планировщик рассылки
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_quote_to_all, trigger='interval', minutes=1, args=[application])
    scheduler.start()

    # Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))

    logging.info("Бот запущен...")
    application.run_polling()
