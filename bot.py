```python
import os
import logging
import random
from datetime import datetime, time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
from pytz import timezone
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

# Еженедельная рефлексия
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

# Отправка цитаты
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in subscribers:
        try:
            quote = random.choice(QUOTES)
            await context.bot.send_message(chat_id=chat_id, text=quote, parse_mode='HTML')
            logger.info(f"Quote sent to {chat_id}")
        except Exception as e:
            logger.error(f"Error sending quote: {e}")

# Отправка рефлексии
async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id=chat_id, text=REFLECTION_TEXT, parse_mode='HTML')
            logger.info(f"Reflection sent to {chat_id}")
        except Exception as e:
            logger.error(f"Error sending reflection: {e}")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌍 Пожалуйста, выбери город из списка, чтобы получать цитаты по своему времени:",
        reply_markup=city_keyboard
    )

# Выбор города
async def city_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    chat_id = update.effective_chat.id
    if city in CITIES:
        tz = CITIES[city]
        subscribers[chat_id] = tz
        await update.message.reply_text(
            "✅ Готово! Вы будете получать стоические цитаты каждый день в 9 утра по выбранному времени.\n\n"
            "🔔 <i>Telegram может по умолчанию отключать уведомления от ботов. "
            "Чтобы не пропустить цитаты — открой настройки чата и включи уведомления.</i>",
            parse_mode='HTML'
        )
        logger.info(f"Subscribed: {chat_id} with tz {tz}")
    else:
        await update.message.reply_text(
            "Пожалуйста, выберите город из списка.",
            reply_markup=city_keyboard
        )

# Команда /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        del subscribers[chat_id]
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
        logger.info(f"Unsubscribed: {chat_id}")
    else:
        await update.message.reply_text("Вы не были подписаны.")

# Основная функция
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, city_choice))

    # Тест: цитаты и рефлексия через 30 сек
    app.job_queue.run_repeating(send_quote, interval=30, first=5)
    app.job_queue.run_repeating(send_reflection, interval=30, first=20)

    # Запуск polling без asyncio.run чтобы избежать конфликта
    return await app.run_polling()

if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
```
