```python
import os
import logging
import random
from datetime import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from stoic_quotes_100 import QUOTES
import pytz

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Токен и хранилище подписчиков: chat_id -> tz
TOKEN = os.getenv("BOT_TOKEN")
subscribers: dict[int, str] = {}

# Команды выбора городов и соответствующих часовых поясов
CITIES = {
    "Москва": "Europe/Moscow",
    "Тбилиси": "Asia/Tbilisi",
    "Рим": "Europe/Rome",
    "Барселона": "Europe/Madrid",
    "Лондон": "Europe/London",
    "Киев": "Europe/Kiev",
    "Самара": "Europe/Samara",
}

# Отправка цитаты
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, tz in subscribers.items():
        try:
            quote = random.choice(QUOTES)
            await context.bot.send_message(chat_id, text=quote, parse_mode='HTML')
            logger.info(f"Quote sent to {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send quote to {chat_id}: {e}")

# Отправка рефлексии
REFLECTION = (
    "🧘‍♂️ *Стоическая неделя. Время для размышлений.*\n"
    "_Эти вопросы не для галочки. Найди несколько минут тишины, чтобы честно взглянуть на прожитую неделю._\n\n"
    "1️⃣ В каких ситуациях я позволил эмоциям взять верх над разумом, и как мог бы отреагировать более мудро?\n"
    "2️⃣ Какие мои действия действительно соответствовали стоическим ценностям, а какие противоречили им?\n"
    "3️⃣ Что из этой недели будет иметь значение через год?\n"
    "4️⃣ Какие возможности послужить другим людям я упустил?\n"
    "5️⃣ Какие препятствия стали возможностями для роста, а какие уроки упустил?"
)

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, tz in subscribers.items():
        try:
            await context.bot.send_message(chat_id, text=REFLECTION, parse_mode='MarkdownV2')
            logger.info(f"Reflection sent to {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send reflection to {chat_id}: {e}")

# /start - выбор города
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[city] for city in CITIES]
    reply = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Пожалуйста, выберите город, чтобы установить ваш часовой пояс:",
        reply_markup=reply,
    )
    logger.info(f"Asked {update.effective_chat.id} to choose city")

# Обработка выбора города через MessageHandler
async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    chat_id = update.effective_chat.id
    if city in CITIES:
        tz = CITIES[city]
        subscribers[chat_id] = tz
        await update.message.reply_text(
            "✅ Готово!\n"
            "Теперь вы будете получать одну мысль из стоицизма каждое утро в 9:00 по вашему времени.\n\n"
            "🔔 Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения.",
            parse_mode='MarkdownV2',
        )
        logger.info(f"Subscribed {chat_id} with tz {tz}")
    else:
        await update.message.reply_text("Город не распознан, попробуйте ещё раз.")

# /stop - отписка
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.pop(chat_id)
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
        logger.info(f"Unsubscribed {chat_id}")
    else:
        await update.message.reply_text("Вы не были подписаны.")

# Настройка расписания
def schedule_jobs(app):
    for chat_id, tz in subscribers.items():
        timezone = pytz.timezone(tz)
        app.job_queue.run_daily(
            send_quote,
            time=time(9, 0),
            tzinfo=timezone,
            name=f"quote_{chat_id}",
            chat_id=chat_id,
        )
        app.job_queue.run_daily(
            send_reflection,
            time=time(12, 0),
            days=(6,),  # воскресенье
            tzinfo=timezone,
            name=f"ref_{chat_id}",
            chat_id=chat_id,
        )

# main
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_city))

    # После инициализации добавим все расписания
    app.job_queue.run_once(lambda ctx: schedule_jobs(app), when=1)

    app.run_polling()

if __name__ == '__main__':
    main()
```
