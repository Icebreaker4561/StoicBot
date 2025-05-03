import os
import logging
import random
from datetime import time
import asyncio

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from stoic_quotes_100 import QUOTES

# ——————————————————————————————————————————————————————————————
# Настройка логирования
logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Карта город → смещение от UTC в часах
TIMEZONE_OFFSETS = {
    'Лермонтов': 3,
    'Батуми': 4,
    'Дюссельдорф': 2,
    'Киев': 3,
    'Барселона': 2,
    'Лиссабон': 1,
}

# chat_id → выбранный город
subscribers: dict[int, str] = {}

# ——————————————————————————————————————————————————————————————
# Шлем цитату
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    city = subscribers.get(chat_id, None)
    offset = TIMEZONE_OFFSETS.get(city, None)
    logger.info(f"Отправляем цитату в чат={chat_id}, город={city!r}, смещение={offset}")
    quote = random.choice(QUOTES)
    await context.bot.send_message(chat_id, quote, parse_mode='HTML')

# Шлем еженедельную рефлексию (по субботам в 12:00 UTC)
REFLECTION_TEXT = (
    "🧘‍♂️ <b>Стоическая неделя</b>\n"
    "<i>Эти вопросы не для галочки. Найди несколько минут тишины...</i>\n\n"
    "1️⃣ В каких ситуациях я позволил эмоциям взять верх над разумом?\n"
    "2️⃣ Какие мои действия соответствовали стоическим ценностям, а какие — нет?\n"
    "3️⃣ Что из того, что я считал важным, действительно будет иметь значение через год?\n"
    "4️⃣ Какие возможности послужить другим я упустил?\n"
    "5️⃣ Какие трудности я смог превратить в возможности для роста?"
)
async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in subscribers:
        logger.info(f"Отправляем еженедельную рефлексию в чат={chat_id}")
        await context.bot.send_message(chat_id, REFLECTION_TEXT, parse_mode='HTML')

# ——————————————————————————————————————————————————————————————
# /start — просим выбрать город
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.info(f"/start от пользователя {chat_id}")
    cities = list(TIMEZONE_OFFSETS.keys())
    keyboard = [[c] for c in cities]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Пожалуйста, выберите ближайший к вам город из списка ниже, чтобы установить часовой пояс 👇",
        reply_markup=markup
    )

# Выбор города — подписываем и планируем
async def setcity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    city = update.message.text.strip()
    if city not in TIMEZONE_OFFSETS:
        await update.message.reply_text("Город не распознан, попробуйте ещё раз.")
        return

    subscribers[chat_id] = city
    offset = TIMEZONE_OFFSETS[city]
    logger.info(f"Пользователь {chat_id} выбрал город={city}, смещение={offset}")

    await update.message.reply_text(
        "✅ Готово!\n"
        f"Теперь Вы будете получать одну мысль от стоиков каждое утро в 13:05 по времени города ({city}).\n\n"
        "🔔⚠️ Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения."
    )

# /stop — отписка
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if subscribers.pop(chat_id, None):
        logger.info(f"Пользователь {chat_id} отписался")
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
    else:
        await update.message.reply_text("Вы не были подписаны.")

# /help
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — подписаться и выбрать город\n"
        "/setcity — изменить город (после команды просто выберите из списка)\n"
        "/stop — отписаться\n"
        "/help — показать это сообщение"
    )

# /share
async def share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Спасибо, что решили поделиться этим ботом 🙏 :)\n\n"
        "Просто перешлите это сообщение другу 👇"
    )
    await update.message.reply_text(
        "Привет! 👋 Хочу рекомендовать тебе классного бота. "
        "Он ежедневно присылает одну стоическую мысль. "
        "Мне очень понравилось: https://t.me/StoicTalesBot?start"
    )

# ——————————————————————————————————————————————————————————————
async def main():
    logger.info("Запуск приложения бота…")
    app = (
        ApplicationBuilder()
        .token(os.getenv("BOT_TOKEN"))
        .build()
    )

    # Регистрируем хендлеры
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setcity", setcity))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("share", share))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, setcity))

    logger.info("Регистрируем задачи планировщика: ежедневная цитата и еженедельная рефлексия")
    # Ежедневная цитата в 13:05 UTC
    app.job_queue.run_daily(send_quote, time=time(hour=13, minute=5))
    logger.info("Запланирована ежедневная отправка цитаты в 13:05 UTC")
    # Еженедельная рефлексия в субботу в 12:00 UTC
    app.job_queue.run_daily(send_reflection, time=time(hour=12, minute=0), days=(6,))
    logger.info("Запланирована еженедельная рефлексия по субботам в 12:00 UTC")

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
