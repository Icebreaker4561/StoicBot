import os
import logging
import random
from datetime import time
import pytz
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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
# Сопоставление городов и часовых поясов
TZ_MAP = {
    'Лермонтов': 'Europe/Moscow',
    'Батуми': 'Asia/Tbilisi',
    'Дюссельдорф': 'Europe/Berlin',
    'Киев': 'Europe/Kiev',
    'Барселона': 'Europe/Madrid',
    'Лиссабон': 'Europe/Lisbon',
}

async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.context
    quote = random.choice(QUOTES)
    try:
        await context.bot.send_message(chat_id, quote, parse_mode='HTML')
        logger.info(f"Quote sent to {chat_id}")
    except Exception as e:
        logger.error(f"Error sending quote to {chat_id}: {e}")

REFLECTION_TEXT = (
    "🧘‍♂️ <b>Стоическая неделя. Время для размышлений.</b>\n"
    "<i>Эти вопросы не для галочки. Найди несколько минут тишины...</i>\n\n"
    "1️⃣ В каких ситуациях я позволил эмоциям взять верх над разумом?\n"
    "2️⃣ Какие мои действия соответствовали стоическим ценностям и принципам, а какие — нет?\n"
    "3️⃣ Что из того, что я считал важным, действительно будет иметь значение через год?\n"
    "4️⃣ Какие возможности послужить другим людям я упустил на этой неделе?\n"
    "5️⃣ Какие препятствия и трудности этой недели я смог превратить в возможности для роста, а какие уроки упустил?"
)

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.context
    try:
        await context.bot.send_message(chat_id, REFLECTION_TEXT, parse_mode='HTML')
        logger.info(f"Reflection sent to {chat_id}")
    except Exception as e:
        logger.error(f"Error sending reflection to {chat_id}: {e}")

# /start: предлагаем выбрать город
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    keyboard = [[city] for city in TZ_MAP.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    text = (
        "Пожалуйста, выберите ближайший к вам город из списка ниже, чтобы установить часовой пояс 👇"
    )
    await update.message.reply_text(text, reply_markup=reply_markup)
    logger.info(f"Prompted city selection for {chat_id}")

# Обработка выбора города и подписка
async def setcity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    city = update.message.text.strip()
    if city not in TZ_MAP:
        await update.message.reply_text("Город не распознан, попробуйте ещё раз.")
        return
    tz_name = TZ_MAP[city]
    # Удаляем старые задания
    for job in context.job_queue.get_jobs():
        if job.name in (f"quote_{chat_id}", f"refl_{chat_id}"):
            job.schedule_removal()
    # Планируем новые задания
    tz = pytz.timezone(tz_name)
    # ежедневная цитата в 12:35 по местному времени
    context.job_queue.run_daily(
        send_quote,
        time=time(hour=12, minute=40, tzinfo=tz),
        days=(0,1,2,3,4,5,6),
        context=chat_id,
        name=f"quote_{chat_id}",
    )
    # еженедельная рефлексия в воскресенье в 12:00
    context.job_queue.run_daily(
        send_reflection,
        time=time(hour=12, minute=0, tzinfo=tz),
        days=(6,),
        context=chat_id,
        name=f"refl_{chat_id}",
    )
    # Подтверждение подписки
    text = (
        "✅ Готово!\n"
        f"Теперь Вы будете получать одну мысль от стоиков каждое утро в 12:40 по времени города {city}.\n\n"
        "🔔⚠️ Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения."
    )
    await update.message.reply_text(text)
    logger.info(f"Subscribed {chat_id} for city {city} ({tz_name})")

# /stop: отписка
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    for job in context.job_queue.get_jobs():
        if job.context == chat_id:
            job.schedule_removal()
    await update.message.reply_text("❌ Вы отписаны от рассылки.")
    logger.info(f"Unsubscribed {chat_id}")

# /help
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - подписаться и выбрать город\n"
        "/stop - отписаться\n"
        "/help - показать справку\n"
        "/share - поделиться ботом"
    )

# /share
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

async def main():
    logger.info("Запуск приложения бота…")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, setcity))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("share", share))
    logger.info("Регистрируем задачи планировщика: ежедневная цитата и еженедельная рефлексия")
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
