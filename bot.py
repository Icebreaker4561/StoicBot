import os
import logging
import random
from datetime import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from stoic_quotes_100 import QUOTES

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Переменные пользователей: chat_id -> timezone string
users_tz = {}
subscribers = set()

# Доступные города и TZ
CITY_TZ = {
    'Москва': 'Europe/Moscow',
    'Киев': 'Europe/Kiev',
    'Тбилиси': 'Asia/Tbilisi',
    'Рим': 'Europe/Rome',
    'Барселона': 'Europe/Madrid',
    'Самара': 'Europe/Samara'
}

# Отправка цитаты
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in list(subscribers):
        tz = users_tz.get(chat_id)
        if not tz:
            continue
        quote = random.choice(QUOTES)
        try:
            await context.bot.send_message(chat_id=chat_id, text=quote, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Ошибка при отправке цитаты {chat_id}: {e}")

# Отправка рефлексии
REFLECTION = (
    "<b>🧘‍♂️ Стоическая неделя. Время для размышлений.</b>\n"
    "<i>Эти вопросы не для галочки. Найди минуту тишины и честно ответь себе:</i>\n"
    "1️⃣ В каких ситуациях эмоции брали верх и как мог отреагировать лучше?\n"
    "2️⃣ Какие действия соответствовали стоицизму, а что противоречило принципам?\n"
    "3️⃣ Что из этого важно через год?\n"
    "4️⃣ Где упустил шанс помочь другим?\n"
    "5️⃣ Какие трудности стали возможностью роста?"
)
async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in list(subscribers):
        tz = users_tz.get(chat_id)
        if not tz:
            continue
        try:
            await context.bot.send_message(chat_id=chat_id, text=REFLECTION, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Ошибка при отправке рефлексии {chat_id}: {e}")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[city] for city in CITY_TZ]
    await update.message.reply_text(
        'Пожалуйста, выберите ваш город:',
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )

# Обработка города
async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    chat_id = update.effective_chat.id
    tz = CITY_TZ.get(city)
    if not tz:
        await update.message.reply_text('Город не распознан, попробуйте ещё раз.')
        return
    users_tz[chat_id] = tz
    subscribers.add(chat_id)
    await update.message.reply_text(
        '✅ Готово!\n'
        'Теперь Вы будете получать одну мысль из стоицизма каждое утро в 9:00.\n\n'
        '🔔 Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения.'
    )
    logger.info(f"Подписка: {chat_id}, TZ={tz}")

# /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers.discard(chat_id)
    users_tz.pop(chat_id, None)
    await update.message.reply_text('❌ Вы отписаны от рассылки.')

# main
def main():
    token = os.getenv('BOT_TOKEN')
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('stop', stop))
    app.add_handler(MessageHandler(filters.Text(list(CITY_TZ.keys())), set_city))

    # Расписание по TZ: цитаты в 9:00 ежедневно
    app.job_queue.run_daily(send_quote, time=time(9,0), tzinfo=None)
    # Рефлексия: воскресенье (6) в 12:00
    app.job_queue.run_daily(send_reflection, time=time(12,0), days=(6,), tzinfo=None)

    app.run_polling()

if __name__ == '__main__':
    main()
