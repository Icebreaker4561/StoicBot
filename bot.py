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

from stoic_quotes_100 import QUOTES  # ваш файл с 100 цитатами

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен из переменных окружения
TOKEN = os.getenv("BOT_TOKEN")

# Хранилище подписчиков: chat_id → выбранный город (позже можно туда класть таймзону)
subscribers: dict[int, str] = {}

# Текст еженедельной рефлексии
REFLECTION_TEXT = (
    "🧘‍♂️ <b>Стоическая неделя</b>\n"
    "<i>Эти вопросы не для галочки. Найди несколько минут тишины...</i>\n\n"
    "1️⃣ В каких ситуациях я позволил эмоциям взять верх над разумом?\n"
    "2️⃣ Какие мои действия соответствовали стоическим ценностям, а какие — нет?\n"
    "3️⃣ Что из того, что я считал важным, действительно будет иметь значение через год?\n"
    "4️⃣ Какие возможности послужить другим я упустил?\n"
    "5️⃣ Какие трудности я смог превратить в возможности для роста?"
)

async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in subscribers:
        quote = random.choice(QUOTES)
        try:
            await context.bot.send_message(chat_id, quote, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка при отправке цитаты {chat_id}: {e}")

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id, REFLECTION_TEXT, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка при отправке рефлексии {chat_id}: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cities = ["Лермонтов", "Батуми", "Дюссельдорф", "Киев", "Барселона", "Лиссабон"]
    keyboard = [[c] for c in cities]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Пожалуйста, выберите ближайший к вам город из списка ниже, чтобы установить часовой пояс 👇",
        reply_markup=reply_markup,
    )
    logger.info(f"{chat_id} запустил /start, предложили выбор города")

async def setcity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    city = update.message.text.strip()
    valid = ["Лермонтов", "Батуми", "Дюссельдорф", "Киев", "Барселона", "Лиссабон"]
    if city not in valid:
        await update.message.reply_text("Город не распознан, попробуйте ещё раз.")
        return

    subscribers[chat_id] = city
    await update.message.reply_text(
        "✅ Готово!\n"
        "Теперь Вы будете получать одну мысль от стоиков каждое утро в 12:20.\n\n"
        "🔔 Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения."
    )
    logger.info(f"{chat_id} подписался на рассылку, город {city}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if subscribers.pop(chat_id, None):
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
        logger.info(f"{chat_id} отписался")
    else:
        await update.message.reply_text("Вы не были подписаны.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — подписаться и выбрать город\n"
        "/stop — отписаться от рассылки\n"
        "/help — показать это сообщение\n"
        "/share — поделиться ботом"
    )

async def share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Спасибо, что решили поделиться этим ботом 🙏\n"
        "Просто перешлите это сообщение другу 👇"
    )
    await update.message.reply_text(
        "Привет! 👋 Хочу рекомендовать тебе этот бот. Он ежедневно присылает одну стоическую мысль: "
        "https://t.me/StoicTalesBot?start"
    )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрация команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, setcity))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("share", share))

    # Расписание: цитаты каждый день в 12:20
    app.job_queue.run_daily(send_quote, time=time(hour=12, minute=20))

    # Рефлексия по воскресеньям
    app.job_queue.run_daily(send_reflection, time=time(hour=12, minute=0), days=(6,))

    # Запускаем бот
    app.run_polling()