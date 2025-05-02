import os
import logging
import random
from datetime import datetime, time
from zoneinfo import ZoneInfo
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from stoic_quotes_100 import QUOTES

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
subscribers = {}  # chat_id: timezone string

CITY_TZ = {
    "Москва": "Europe/Moscow",
    "Тбилиси": "Asia/Tbilisi",
    "Рим": "Europe/Rome",
    "Барселона": "Europe/Madrid",
    "Лондон": "Europe/London",
    "Киев": "Europe/Kyiv",
    "Самара": "Europe/Samara"
}

REFLECTION_TEXT = (
    "🧘‍♂️ Стоическая неделя. Время для размышлений.\n\n"
    "Эти вопросы не для галочки. Найди несколько минут тишины, чтобы честно взглянуть на прожитую неделю. Ответы не обязательны — но они могут многое изменить в твоей жизни.\n\n"
    "1️⃣ В каких ситуациях на этой неделе я позволил эмоциям взять верх над разумом, и как мог бы отреагировать более мудро, мужественно, справедливо и умеренно?\n"
    "2️⃣ Какие мои действия действительно соответствовали стоическим ценностям и принципам, а какие шли вразрез с ними?\n"
    "3️⃣ Что из того, что я считал важным на этой неделе, действительно будет иметь значение через год?\n"
    "4️⃣ Какие возможности послужить другим людям я упустил на этой неделе?\n"
    "5️⃣ Какие препятствия и трудности этой недели я смог превратить в возможности для роста, а какие уроки упустил?"
)

async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, tz_name in subscribers.items():
        tz = ZoneInfo(tz_name)
        now = datetime.now(tz)
        if now.hour == 9 and now.minute == 0:
            quote = random.choice(QUOTES)
            try:
                await context.bot.send_message(chat_id, quote, parse_mode='HTML')
            except Exception as e:
                logger.error(f"Ошибка при отправке цитаты {chat_id}: {e}")

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, tz_name in subscribers.items():
        tz = ZoneInfo(tz_name)
        now = datetime.now(tz)
        if now.weekday() == 6 and now.hour == 12 and now.minute == 0:
            try:
                await context.bot.send_message(chat_id, REFLECTION_TEXT, parse_mode='HTML')
            except Exception as e:
                logger.error(f"Ошибка при отправке рефлексии {chat_id}: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[c] for c in CITY_TZ.keys()]
    await update.message.reply_text(
        "✅ Готово!\nТеперь Вы будете получать одну мысль из стоицизма каждое утро в 9:00.\n\n"
        "🔔 Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения.\n\n"
        "Пожалуйста, выберите ваш город:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )

async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text.strip()
    chat_id = update.effective_chat.id
    if city in CITY_TZ:
        subscribers[chat_id] = CITY_TZ[city]
        await update.message.reply_text(f"Часовой пояс установлен: {CITY_TZ[city]}")
        logger.info(f"Пользователь {chat_id} подписан с TZ: {CITY_TZ[city]}")
    else:
        await update.message.reply_text("Не удалось определить город. Пожалуйста, выберите из списка.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.pop(chat_id)
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
        logger.info(f"Пользователь {chat_id} отписан")
    else:
        await update.message.reply_text("Вы не были подписаны.")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_city))

    app.job_queue.run_repeating(send_quote, interval=60)
    app.job_queue.run_repeating(send_reflection, interval=60)

    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
