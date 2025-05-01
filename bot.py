import os
import logging
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from pytz import timezone
from datetime import datetime
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

CITIES = {
    "Тбилиси": "Asia/Tbilisi",
    "Москва": "Europe/Moscow",
    "Киев": "Europe/Kyiv",
    "Самара": "Europe/Samara",
    "Барселона": "Europe/Madrid",
    "Лондон": "Europe/London",
    "Рим": "Europe/Rome"
}

city_keyboard = ReplyKeyboardMarkup(
    [[city] for city in CITIES],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Рефлексия
REFLECTION_TEXT = (
    "<b>🧠 Стоическая неделя. Время для размышлений.</b>\n\n"
    "<i>Эти вопросы не для галочки. Найди несколько минут тишины, чтобы честно взглянуть на прожитую неделю. "
    "Ответы не обязательны — но они могут многое изменить в твоей жизни.</i>\n\n"
    "1️⃣ В каких ситуациях на этой неделе я позволил эмоциям взять верх над разумом, и как мог бы отреагировать более мудро, мужественно, справедливо и умеренно?\n"
    "2️⃣ Какие мои действия действительно соответствовали стоическим ценностям и принципам, а какие шли вразрез с ними?\n"
    "3️⃣ Что из того, что я считал важным на этой неделе, действительно будет иметь значение через год?\n"
    "4️⃣ Какие возможности послужить другим людям я упустил на этой неделе?\n"
    "5️⃣ Какие препятствия и трудности этой недели я смог превратить в возможности для роста, а какие уроки упустил?"
)

# Цитата
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in subscribers:
        try:
            quote = random.choice(QUOTES)
            await context.bot.send_message(chat_id=chat_id, text=quote, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Ошибка отправки цитаты: {e}")

# Рефлексия
async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id=chat_id, text=REFLECTION_TEXT, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Ошибка отправки рефлексии: {e}")

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌍 Пожалуйста, выбери город из списка, чтобы получать цитаты по своему времени:", reply_markup=city_keyboard)

async def city_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    chat_id = update.effective_chat.id

    if city in CITIES:
        tz = CITIES[city]
        subscribers[chat_id] = tz
        await update.message.reply_text(
            "✅ Готово! Вы будете получать стоические цитаты каждый день в 9 утра по выбранному времени.\n\n"
            "🔔 <i>Telegram может по умолчанию отключать уведомления от ботов. Чтобы получать стоические цитаты каждое утро — откройте настройки этого чата и включите уведомления.</i>",
            parse_mode='HTML'
        )
        logger.info(f"Подписан: {chat_id} в часовом поясе {tz}")
    else:
        await update.message.reply_text("Пожалуйста, выбери город только из предложенного списка.", reply_markup=city_keyboard)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        del subscribers[chat_id]
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
        logger.info(f"Отписан: {chat_id}")
    else:
        await update.message.reply_text("Вы не были подписаны.")

# Запуск
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, city_choice))

    # Цитаты каждые 30 сек, рефлексия — каждые 30 сек (чередуется)
    app.job_queue.run_repeating(send_quote, interval=60, first=5)
    app.job_queue.run_repeating(send_reflection, interval=60, first=35)

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.get_event_loop().run_until_complete(main())