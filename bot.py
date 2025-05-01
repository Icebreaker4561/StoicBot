import os
import logging
import random
from datetime import datetime, time
from zoneinfo import ZoneInfo
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from stoic_quotes_100 import QUOTES

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Переменные
TOKEN = os.getenv("BOT_TOKEN")
users = {}  # chat_id -> timezone

# Отправка цитаты
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    if chat_id in users:
        quote = random.choice(QUOTES)
        try:
            await context.bot.send_message(chat_id=chat_id, text=quote, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Ошибка при отправке цитаты {chat_id}: {e}")

# Отправка рефлексии
REFLECTION_TEXT = (
    "🧘‍♂️ *Стоическая неделя. Время для размышлений.*\n"
    "Эти вопросы не для галочки. Найди несколько минут тишины...\n"
    "1️⃣ ...?\n"
    "2️⃣ ...?\n"
    "3️⃣ ...?\n"
    "4️⃣ ...?\n"
    "5️⃣ ...?"
)
async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    try:
        await context.bot.send_message(chat_id=chat_id, text=REFLECTION_TEXT, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Ошибка при отправке рефлексии {chat_id}: {e}")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [[KeyboardButton(c)] for c in ['Москва','Киев','Самара','Тбилиси','Рим','Барселона','Лондон']]
    await update.message.reply_text(
        "➡️ Пожалуйста, выбери город из списка, используй кнопки:",
        reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
    )

# Выбор города
async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    tz_map = {
        'Москва':'Europe/Moscow', 'Киев':'Europe/Kiev', 'Самара':'Europe/Samara',
        'Тбилиси':'Asia/Tbilisi','Рим':'Europe/Rome','Барселона':'Europe/Madrid','Лондон':'Europe/London'
    }
    if city not in tz_map:
        await update.message.reply_text('Город не распознан, попробуйте ещё раз.')
        return
    tz = tz_map[city]
    chat_id = update.effective_chat.id
    users[chat_id] = tz
    # сброс старых заданий
    app = context.application
    app.job_queue.get_jobs_by_name(f"quote_{chat_id}") and [job.schedule_removal() for job in app.job_queue.get_jobs_by_name(f"quote_{chat_id}")]
    app.job_queue.get_jobs_by_name(f"refl_{chat_id}") and [job.schedule_removal() for job in app.job_queue.get_jobs_by_name(f"refl_{chat_id}")]
    # новые расписания
    tzinfo = ZoneInfo(tz)
    app.job_queue.run_daily(send_quote, time=time(9,0,tzinfo=tzinfo), chat_id=chat_id, name=f"quote_{chat_id}")
    app.job_queue.run_daily(send_reflection, time=time(12,0,tzinfo=tzinfo), days=(6,), chat_id=chat_id, name=f"refl_{chat_id}")
    # подтверждение
    await update.message.reply_text(
        "✅ Готово!\nТеперь Вы будете получать одну мысль из стоицизма каждое утро в 9:00.\n"
        "🔔 Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения.",
        parse_mode='Markdown'
    )
    logger.info(f"Подписан: {chat_id} TZ={tz}")

# Команда /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in users:
        users.pop(chat_id)
        for job in context.application.job_queue.get_jobs_by_name(f"quote_{chat_id}") + context.application.job_queue.get_jobs_by_name(f"refl_{chat_id}"):
            job.schedule_removal()
        await update.message.reply_text('❌ Вы отписаны.')
    else:
        await update.message.reply_text('Этот чат не был подписан.')

# Основная функция
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_city))
    app.add_handler(CommandHandler('stop', stop))
    app.run()  # run() вместо run_polling() для рендера

if __name__ == '__main__':
    main()
