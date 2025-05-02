import os
import logging
import random
from datetime import time
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackContext,
)
from stoic_quotes_100 import QUOTES

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Список подписчиков
subscribers = set()

# Функция отправки цитаты
async def send_quote(context: CallbackContext):
    for chat_id in subscribers:
        try:
            quote = random.choice(QUOTES)
            await context.bot.send_message(chat_id, quote, parse_mode='HTML')
            logger.info(f"Отправлена цитата в {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке цитаты {chat_id}: {e}")

# Функция отправки недельной рефлексии
REFLECTION = (
    "🧘‍♂️ *Стоическая неделя*\n"
    "_Эти вопросы не для галочки. Найди несколько минут тишины._\n\n"
    "1️⃣ В каких ситуациях я позволил эмоциям взять верх над разумом?\n"
    "2️⃣ Какие мои действия соответствовали стоическим ценностям, а какие нет?\n"
    "3️⃣ Что из того, что я считал важным, будет иметь значение через год?\n"
    "4️⃣ Какие возможности помочь другим я упустил?\n"
    "5️⃣ Какие трудности этой недели я смог превратить в рост?"
)

async def send_reflection(context: CallbackContext):
    for chat_id in subscribers:
        try:
            await context.bot.send_message(
                chat_id,
                REFLECTION,
                parse_mode='Markdown'
            )
            logger.info(f"Отправлена рефлексия в {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке рефлексии {chat_id}: {e}")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers.add(chat_id)
    await update.message.reply_text(
        "✅ Готово!\n"
        "Теперь Вы будете получать одну мысль из стоицизма каждое утро в 9:00.\n\n"
        "🔔 Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения."
    )
    logger.info(f"Подписался: {chat_id}")

# Команда /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        await update.message.reply_text("❌ Вы отписаны.")
        logger.info(f"Отписался: {chat_id}")
    else:
        await update.message.reply_text("Вы и так не были подписаны.")

# Точка входа
if __name__ == '__main__':
    TOKEN = os.getenv('BOT_TOKEN')
    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрируем команды
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('stop', stop))

    # Планировщик цитат: каждое утро в 9:00
    app.job_queue.run_daily(
        send_quote,
        time=time(hour=9, minute=0),
        days=(0,1,2,3,4,5,6),
    )
    # Планировщик рефлексии: воскресенье в 12:00
    app.job_queue.run_daily(
        send_reflection,
        time=time(hour=12, minute=0),
        days=(6,),
    )

    # Запуск polling
    app.run_polling()
