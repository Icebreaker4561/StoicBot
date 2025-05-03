import os
import logging
import random
from datetime import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from stoic_quotes_100 import QUOTES  # ваш список цитат

# ——— Настройка логирования ———
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")

# Здесь будем хранить chat_id → выбранный город (потом — и TZ)
subscribers: dict[int, str] = {}

# ——— Функции рассылки ———

async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in subscribers:
        quote = random.choice(QUOTES)
        await context.bot.send_message(chat_id, quote)

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🧘‍♂️ *Стоическая неделя*\n"
        "_Эти вопросы не для галочки, найдите минуту тишины_\n\n"
        "1️⃣ Где эмоции победили разум?\n"
        "2️⃣ Что шло вразрез стоическим ценностям?\n"
        "3️⃣ Что действительно важно через год?\n"
        "4️⃣ Кого я мог поддержать, но не сделал этого?\n"
        "5️⃣ Какие трудности стали вашим ростом?"
    )
    for chat_id in subscribers:
        await context.bot.send_message(chat_id, text, parse_mode="Markdown")

# ——— Обработчики команд ———

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cities = ["Лермонтов","Батуми","Дюссельдорф","Киев","Барселона","Лиссабон"]
    kb = [[c] for c in cities]
    await update.message.reply_text(
        "Пожалуйста, выберите ближайший к вам город из списка ниже, чтобы установить часовой пояс 👇",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )

async def setcity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    city = update.message.text.strip()
    if city not in ["Лермонтов","Батуми","Дюссельдорф","Киев","Барселона","Лиссабон"]:
        return await update.message.reply_text("Город не распознан, попробуйте ещё раз.")
    subscribers[chat_id] = city
    await update.message.reply_text(
        "✅ Готово!\n"
        "Теперь Вы будете получать одну мысль от стоиков каждое утро в 11:05 по времени города "
        f"({city}).\n\n"
        "🔔 Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения."
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if subscribers.pop(chat_id, None):
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
    else:
        await update.message.reply_text("Вы не были подписаны.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — подписаться и выбрать город\n"
        "/setcity — поменять город\n"
        "/stop — отписаться\n"
        "/share — рассказать о боте\n"
        "/help — справка"
    )

async def share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Спасибо, что решили поделиться этим ботом 🙏 :)\n"
        "Просто перешлите это сообщение другу 👇"
    )
    await update.message.reply_text(
        "Привет! 👋 Хочу рекомендовать тебе классного бота. "
        "Он ежедневно присылает одну стоическую мысль. "
        "Мне очень понравилось: https://t.me/StoicTalesBot_dev_bot?start"
    )

# ——— Точка входа ———

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрация команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setcity", setcity))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("share", share))

    # Планировщик: цитата каждый день в 11:15 ежедневно
    app.job_queue.run_daily(send_quote, time=time(hour=11, minute=15), days=(0,1,2,3,4,5,6))

    # Рефлексия каждое воскресенье в 12:00
    app.job_queue.run_daily(send_reflection, time=time(hour=12, minute=0), days=(6,))

    # Запуск поллинга
    app.run_polling()

if __name__ == "__main__":
    main()