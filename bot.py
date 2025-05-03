import os
import logging
import random
from datetime import time
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from stoic_quotes_100 import QUOTES

# --- Настройка логирования ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Токен бота ---
TOKEN = os.getenv("BOT_TOKEN")

# --- Хранилище подписок: chat_id -> город ---
subscribers: dict[int, str] = {}

# --- Отправка цитаты ---
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, city in subscribers.items():
        quote = random.choice(QUOTES)
        try:
            await context.bot.send_message(
                chat_id,
                f"{quote}\n\n— <i>{city}</i>",
                parse_mode="HTML",
            )
            logger.info(f"Sent quote to {chat_id} ({city})")
        except Exception as e:
            logger.error(f"Failed to send quote to {chat_id}: {e}")

# --- Текст еженедельной рефлексии ---
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
        try:
            await context.bot.send_message(
                chat_id, REFLECTION_TEXT, parse_mode="HTML"
            )
            logger.info(f"Sent reflection to {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send reflection to {chat_id}: {e}")

# --- /start: спрашиваем город ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cities = ["Лермонтов", "Батуми", "Дюссельдорф", "Киев", "Барселона", "Лиссабон"]
    keyboard = [[c] for c in cities]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(
        "Пожалуйста, выберите ближайший к вам город из списка ниже, чтобы установить часовой пояс 👇",
        reply_markup=reply_markup,
    )
    logger.info(f"Prompted city selection for {chat_id}")

# --- /setcity: сохраняем выбор города ---
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
        f"Теперь Вы будете получать одну мысль от стоиков каждое утро в 11:50 по времени города ({city}).\n\n"
        "🔔⚠️ Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения."
    )
    logger.info(f"Subscribed {chat_id} with city {city}")

# --- /stop: отписаться ---
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.pop(chat_id)
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
        logger.info(f"Unsubscribed {chat_id}")
    else:
        await update.message.reply_text("Вы не были подписаны.")

# --- /help: список команд ---
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — подписаться и выбрать город\n"
        "/setcity — изменить город (наберите название из списка)\n"
        "/stop — отписаться от рассылки\n"
        "/share — поделиться ботом с другом\n"
        "/help — показать это сообщение"
    )

# --- /share: две последовательных реплики ---
async def share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Спасибо, что решили поделиться этим ботом 🙏 :)\n"
        "Просто перешлите это сообщение другу 👇"
    )
    await update.message.reply_text(
        "Привет! 👋 Хочу рекомендовать тебе классного бота. "
        "Он ежедневно присылает одну стоическую мысль. "
        "Мне очень понравилось: https://t.me/StoicTalesBot?start"
    )
    logger.info(f"Share requested by {update.effective_chat.id}")

# --- Основная функция и запуск ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрируем обработчики команд и текста
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setcity", setcity))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("share", share))
    # Все остальные текстовые сообщения — считаем, что это выбор города
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, setcity))

    # Планируем ежедневную рассылку цитат в 11:50 по всем дням недели
    app.job_queue.run_daily(
        send_quote,
        time=time(hour=11, minute=50),
        days=(0, 1, 2, 3, 4, 5, 6),
    )
    # Планируем еженедельную рефлексию в воскресенье (6) в 12:00
    app.job_queue.run_daily(
        send_reflection,
        time=time(hour=12, minute=0),
        days=(6,),
    )

    # Запускаем long-polling
    app.run_polling()

if __name__ == "__main__":
    main()