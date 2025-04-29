import os
import random
from datetime import datetime, timedelta

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from stoic_quotes_100 import QUOTES

BOT_TOKEN = os.getenv("BOT_TOKEN")

TIMEZONES = {
    "Лондон": 1,
    "Рим": 2,
    "Барселона": 2,
    "Киев": 3,
    "Москва": 3,
    "Самара": 4,
    "Тбилиси": 4
}

users = {}

app = ApplicationBuilder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[city] for city in TIMEZONES.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    welcome_text = (
        "⏰ Чтобы получать стоические цитаты ровно в 9 утра по вашему времени,\n"
        "пожалуйста, выберите ближайший к вам город из списка ниже:"
    )

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def handle_city_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_city = update.message.text
    chat_id = update.message.chat_id

    if user_city in TIMEZONES:
        timezone = TIMEZONES[user_city]
        users[chat_id] = timezone
        await update.message.reply_text(
            f"✅ Отлично! Теперь ты будешь получать цитаты каждый день в 9:00 утра по времени {user_city}."
        )
    else:
        await update.message.reply_text(
            "🚫 Пожалуйста, выбери город из списка, используя кнопки."
        )

async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[city] for city in TIMEZONES.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "🌍 Выберите новый город для корректного времени рассылки:",
        reply_markup=reply_markup
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in users:
        del users[chat_id]
        await update.message.reply_text("🛑 Вы отписались от ежедневных рассылок цитат.")
    else:
        await update.message.reply_text("ℹ️ Вы ещё не были подписаны.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 Этот бот присылает стоические цитаты каждый день в 9 утра по вашему времени.\n\n"
        "📌 Доступные команды:\n"
        "/start — подписаться на рассылку\n"
        "/stop — остановить рассылку\n"
        "/setcity — изменить выбранный город\n"
        "/share — поделиться ботом с друзьями\n"
        "/help — показать это сообщение"
    )
    await update.message.reply_text(help_text)

async def share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    share_text = (
        "📬 Хочешь поделиться стоической мудростью?\n\n"
        "Отправь эту ссылку своим друзьям:\n"
        "👉 https://t.me/StoicTalesBot"
    )
    await update.message.reply_text(share_text)

async def send_daily_quotes():
    now_utc = datetime.utcnow()
    for chat_id, timezone_offset in users.items():
        user_time = now_utc + timedelta(hours=timezone_offset)
        if True:  # !!! Для теста отправляем КАЖДУЮ минуту !!!
            quote = random.choice(QUOTES)
            try:
                await app.bot.send_message(chat_id=chat_id, text=quote, parse_mode="HTML")
                print(f"Цитата отправлена пользователю {chat_id}")
            except Exception as e:
                print(f"Ошибка отправки сообщения пользователю {chat_id}: {e}")

scheduler = AsyncIOScheduler()
scheduler.add_job(send_daily_quotes, "interval", minutes=1)
scheduler.start()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("setcity", set_city))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("share", share))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city_choice))

if __name__ == "__main__":
    app.run_polling()