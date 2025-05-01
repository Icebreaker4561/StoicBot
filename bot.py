import os
import logging
import random
from datetime import datetime, time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from stoic_quotes_100 import QUOTES

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Переменные
TOKEN = os.getenv("BOT_TOKEN")
subscribers = {}

# Стадии выбора города
CITY, = range(1)

# Доступные города и часовые пояса
TIME_ZONES = {
    'Москва': +3,
    'Киев': +3,
    'Тбилиси': +4,
    'Самара': +4,
    'Лондон': 0,
    'Рим': +2,
    'Барселона': +2,
}

# Функция отправки цитаты
async def send_quote_job(chat_id, tz_offset, context):
    quote = random.choice(QUOTES)
    try:
        await context.bot.send_message(chat_id=chat_id, text=quote, parse_mode='HTML')
        logger.info(f"Цитата отправлена в {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке цитаты: {e}")

# Функция отправки рефлексии
REFLECTION = (
    "🧘‍♂️ <b>Стоическая неделя. Время для размышлений.</b>\n"
    "Эти вопросы не для галочки. Найди несколько минут тишины, чтобы честно взглянуть на прожитую неделю. Ответы не обязательны — но они могут многое изменить в твоей жизни.\n\n"
    "1️⃣ В каких ситуациях на этой неделе я позволил эмоциям взять верх над разумом, и как мог бы отреагировать более мудро, мужественно, справедливо и умеренно?\n"
    "2️⃣ Какие мои действия действительно соответствовали стоическим ценностям и принципам, а какие шли вразрез с ними?\n"
    "3️⃣ Что из того, что я считал важным на этой неделе, действительно будет иметь значение через год?\n"
    "4️⃣ Какие возможности послужить другим людям я упустил на этой неделе?\n"
    "5️⃣ Какие препятствия и трудности этой недели я смог превратить в возможности для роста, а какие уроки упустил?"
)

async def send_reflection_job(chat_id, context):
    try:
        await context.bot.send_message(chat_id=chat_id, text=REFLECTION, parse_mode='HTML')
        logger.info(f"Рефлексия отправлена в {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке рефлексии: {e}")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup([list(TIME_ZONES.keys())], one_time_keyboard=True)
    await update.message.reply_text(
        'Пожалуйста, выберите город из списка:',
        reply_markup=reply_markup
    )
    return CITY

async def city_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    city = update.message.text
    if city not in TIME_ZONES:
        await update.message.reply_text('Город не распознан, попробуйте еще раз.')</code>
        return CITY
    tz = TIME_ZONES[city]
    subscribers[chat_id] = tz
    # Запланировать job
    now = datetime.utcnow()
    sched = context.job_queue
    sched.run_daily(send_quote_job, time=time(0,0), days=(0,1,2,3,4,5,6), context=(chat_id, tz))
    sched.run_weekly(send_reflection_job, time=time(0,0), day_of_week='sun', context=chat_id)

    await update.message.reply_text(
        '✅ Готово! Вы будете получать стоические цитаты каждый день в 9 утра по выбранному времени.\n'
        '\n'
        '🔔 Убедитесь, что уведомления от этого бота включены в настройках чата.'
    )
    return ConversationHandler.END

# /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        del subscribers[chat_id]
        await update.message.reply_text('❌ Вы отписаны от рассылки.')
    else:
        await update.message.reply_text('Вы не были подписаны.')

# Главная функция
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city_chosen)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('stop', stop))

    app.run_forever()

if __name__ == '__main__':
    main()
