import os
import logging
import random
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from pytz import timezone
from apscheduler.triggers.cron import CronTrigger
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

# Города и часовые пояса
CITY_TIMEZONES = {
    "Тбилиси": "Asia/Tbilisi",
    "Москва": "Europe/Moscow",
    "Киев": "Europe/Kyiv",
    "Самара": "Europe/Samara",
    "Лондон": "Europe/London",
    "Рим": "Europe/Rome",
    "Барселона": "Europe/Madrid"
}

CITY_KEYBOARD = ReplyKeyboardMarkup(
    [[city] for city in CITY_TIMEZONES.keys()],
    one_time_keyboard=True,
    resize_keyboard=True
)

# Цитаты
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, tz in subscribers.items():
        quote = random.choice(QUOTES)
        try:
            await context.bot.send_message(chat_id=chat_id, text=quote, parse_mode='HTML')
            logger.info(f"Цитата отправлена в {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке цитаты: {e}")

# Рефлексия
REFLECTION_TEXT = (
    "🧘‍♂️ <b>Стоическая неделя. Время для размышлений.</b>\n\n"
    "Эти вопросы не для галочки. Найди несколько минут тишины, чтобы честно взглянуть на прожитую неделю."
    " Ответы не обязательны — но они могут многое изменить в твоей жизни.\n\n"
    "1️⃣ В каких ситуациях на этой неделе я позволил эмоциям взять верх над разумом, и как мог бы отреагировать более мудро, мужественно, справедливо и умеренно?\n"
    "2️⃣ Какие мои действия действительно соответствовали стоическим ценностям и принципам, а какие шли вразрез с ними?\n"
    "3️⃣ Что из того, что я считал важным на этой неделе, действительно будет иметь значение через год?\n"
    "4️⃣ Какие возможности послужить другим людям я упустил на этой неделе?\n"
    "5️⃣ Какие препятствия и трудности этой недели я смог превратить в возможности для роста, а какие уроки упустил?"
)

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id=chat_id, text=REFLECTION_TEXT, parse_mode='HTML')
            logger.info(f"Рефлексия отправлена в {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка рефлексии: {e}")

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        "👋 Добро пожаловать! Пожалуйста, выбери город из списка, используя кнопки:",
        reply_markup=CITY_KEYBOARD
    )

async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        "📍 Пожалуйста, выбери свой город заново:",
        reply_markup=CITY_KEYBOARD
    )

async def handle_city_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    city = update.message.text
    if city in CITY_TIMEZONES:
        tz = CITY_TIMEZONES[city]
        subscribers[chat_id] = tz
        await update.message.reply_text("✅ Готово! Вы будете получать стоические цитаты каждый день в 9 утра по выбранному времени.

🔔 _Telegram может по умолчанию отключать уведомления от ботов. Чтобы получать стоические цитаты каждое утро — откройте настройки этого чата и включите уведомления._")
        logger.info(f"Подписан: {chat_id} в часовом поясе {tz}")
    else:
        await update.message.reply_text("Пожалуйста, выбери город из предложенного списка.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        del subscribers[chat_id]
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
        logger.info(f"Отписался: {chat_id}")
    else:
        await update.message.reply_text("Вы еще не подписались на этот канал.")

# main
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("city", set_city))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_city_choice))

    app.job_queue.run_repeating(send_quote, interval=120, first=10)
    app.job_queue.run_repeating(send_reflection, interval=120, first=60)

    app.run_polling()

if __name__ == "__main__":
    main()
