import os
import logging
import random
from datetime import datetime, time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from stoic_quotes_100 import QUOTES

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = os.getenv("BOT_TOKEN")

# Хранилище подписчиков: chat_id -> tz_name
subscribers = {}

# Рассылка цитаты
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.utcnow()
    for chat_id, tz in subscribers.items():
        # тут можно учесть tz, но пока просто шлём
        quote = random.choice(QUOTES)
        try:
            await context.bot.send_message(chat_id=chat_id, text=quote, parse_mode='HTML')
            logger.info(f"Quote sent to {chat_id}")
        except Exception as e:
            logger.error(f"Error sending quote to {chat_id}: {e}")

# Еженедельная рефлексия
REFLECTION_TEXT = (
    "🧘‍♂️ <b>Стоическая неделя</b>\n"
    "<i>Эти вопросы не для галочки. Найди несколько минут тишины, чтобы честно взглянуть на прожитую неделю.</i>\n"
    "1️⃣ В каких ситуациях на этой неделе я позволил эмоциям взять верх над разумом, и как мог бы отреагировать более мудро, мужественно, справедливо и умеренно?\n"
    "2️⃣ Какие мои действия действительно соответствовали стоическим ценностям и принципам, а какие шли вразрез с ними?\n"
    "3️⃣ Что из того, что я считал важным на этой неделе, действительно будет иметь значение через год?\n"
    "4️⃣ Какие возможности послужить другим людям я упустил на этой неделе?\n"
    "5️⃣ Какие препятствия и трудности этой недели я смог превратить в возможности для роста, а какие уроки упустил?"
)

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id=chat_id, text=REFLECTION_TEXT, parse_mode='HTML')
            logger.info(f"Reflection sent to {chat_id}")
        except Exception as e:
            logger.error(f"Error sending reflection to {chat_id}: {e}")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # Предложим выбрать город/часовой пояс
    cities = ['Москва', 'Тбилиси', 'Рим', 'Барселона', 'Лондон', 'Киев', 'Самара']
    keyboard = [[c] for c in cities]
    reply = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "✅ Готово!\nТеперь Вы будете получать одну мысль из стоицизма каждое утро в 9:00.\n\n"
        "🔔 Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения.\n\n"
        "Пожалуйста, выберите город из списка ниже, чтобы установить ваш часовой пояс:",
        reply_markup=reply
    )

# Обработка выбора города
async def setcity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text.strip()
    chat_id = update.effective_chat.id
    # Сохраним выбор, для простоты tz=city
    subscribers[chat_id] = city
    await update.message.reply_text(f"Город установлен: {city}. Спасибо! Используйте /help для списка команд.")
    logger.info(f"User {chat_id} set city: {city}")

# /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.pop(chat_id, None)
        await update.message.reply_text("❌ Вы отписаны.")
    else:
        await update.message.reply_text("Вы не были подписаны.")

# /help
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "/start - подписаться и выбрать город\n"
        "/stop - отписаться от рассылки\n"
        "/setcity - изменить город/часовой пояс\n"
        "/share - поделиться ботом с друзьями\n"
        "/help - показать это сообщение"
    )
    await update.message.reply_text(text)

# /share
async def share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start"
    await update.message.reply_text(f"Поделитесь ботом с друзьями: {link}")

# main
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("share", share))
    app.add_handler(CommandHandler("setcity", setcity))
    app.add_handler(MessageHandler(filters.Regex('^(Москва|Тбилиси|Рим|Барселона|Лондон|Киев|Самара)$'), setcity))

    # Расписание: цитаты каждый день в 9:00
    app.job_queue.run_daily(send_quote, time=time(hour=9, minute=0))
    # Еженедельная рефлексия: воскресенье в 12:00
    app.job_queue.run_daily(send_reflection, time=time(hour=12, minute=0), days=(6,))

    app.run_polling()

if __name__ == "__main__":
    main()
