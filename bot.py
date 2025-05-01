```python
import os
import logging
import random
from datetime import datetime, time, timedelta
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    JobQueue,
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
subscribers = {}  # chat_id -> timezone offset
CITIES = {
    "Moscow": 3,
    "Samara": 4,
    "Kiev": 2,
    "Tbilisi": 4,
    "Rome": 1,
    "Barcelona": 2,
    "London": 1,
}

# Отправка цитаты
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    now_utc = datetime.utcnow()
    for chat_id, tz in subscribers.items():
        local_time = now_utc + timedelta(hours=tz)
        if local_time.hour == 9 and local_time.minute == 0:
            quote = random.choice(QUOTES)
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=quote,
                    parse_mode='HTML'
                )
                logger.info(f"Цитата отправлена в {chat_id}")
            except Exception as e:
                logger.error(f"Ошибка при отправке цитаты в {chat_id}: {e}")

# Отправка рефлексии по воскресеньям
async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    now_utc = datetime.utcnow()
    if now_utc.weekday() == 6 and now_utc.hour == 12 and now_utc.minute == 0:
        for chat_id in subscribers:
            try:
                text = (
                    "🧘‍♂️ Стоическая неделя. Время для размышлений.\n\n"
                    "Эти вопросы не для галочки. Найди несколько минут тишины, чтобы честно взглянуть на прожитую неделю. Ответы не обязательны — но они могут многое изменить в твоей жизни.\n\n"
                    "1️⃣ В каких ситуациях я позволил эмоциям взять верх над разумом, и как мог бы отреагировать более мудро, мужественно, справедливо и умеренно?\n"
                    "2️⃣ Какие мои действия действительно соответствовали стоическим ценностям и принципам, а какие шли вразрез с ними?\n"
                    "3️⃣ Что из того, что я считал важным на этой неделе, действительно будет иметь значение через год?\n"
                    "4️⃣ Какие возможности послужить другим людям я упустил на этой неделе?\n"
                    "5️⃣ Какие препятствия и трудности этой недели я смог превратить в возможности для роста, а какие уроки упустил?"
                )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode='HTML'
                )
                logger.info(f"Рефлексия отправлена в {chat_id}")
            except Exception as e:
                logger.error(f"Ошибка при отправке рефлексии в {chat_id}: {e}")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # Предложим выбрать город
    keyboard = ReplyKeyboardMarkup(
        [[city] for city in CITIES.keys()],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    await update.message.reply_text(
        "Пожалуйста, выберите город для расчета времени рассылки:",
        reply_markup=keyboard
    )

# Обработка выбора города
async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    chat_id = update.effective_chat.id
    if city in CITIES:
        subscribers[chat_id] = CITIES[city]
        await update.message.reply_text(
            "✅ Готово! Вы будете получать стоические цитаты каждый день в 9 утра по выбранному времени.\n"
            "🔔 Telegram может по умолчанию отключать уведомления от ботов. Чтобы ничего не пропустить, включите уведомления для этого чата."
        )
        logger.info(f"Подписан: {chat_id}, город: {city}, TZ: {CITIES[city]}")
    else:
        await update.message.reply_text("Город не распознан, попробуйте еще раз.")

# Команда /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.pop(chat_id)
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
    else:
        await update.message.reply_text("Вы не были подписаны.")
    logger.info(f"Отписался: {chat_id}")

# Главная функция
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_city))

    jq: JobQueue = app.job_queue
    jq.run_repeating(send_quote, interval=30, first=5)
    jq.run_repeating(send_reflection, interval=30, first=15)

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```
