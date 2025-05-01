import os
import logging
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from stoic_quotes_100 import QUOTES

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Множество подписчиков (chat_id)
subscribers = set()

# Функция отправки цитаты
async def send_quote(context: ContextTypes.DEFAULT_TYPE):
    if not subscribers:
        return
    quote = random.choice(QUOTES)
    for chat_id in list(subscribers):
        try:
            await context.bot.send_message(chat_id=chat_id, text=quote, parse_mode='HTML')
            logger.info(f"Quote sent to {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send quote to {chat_id}: {e}")

# Функция отправки рефлексии
REFLECTION_TEXT = (
    "🧘‍♂️ <b>Стоическая неделя. Время для размышлений.</b>\n"
    "Эти вопросы не для галочки. Найди несколько минут тишины, чтобы честно взглянуть на прожитую неделю. Ответы не обязательны — но они могут многое изменить.\n\n"
    "1️⃣ <i>В каких ситуациях я позволил эмоциям взять верх над разумом, и как мог бы отреагировать более мудро, мужественно, справедливо и умеренно?</i>\n"
    "2️⃣ <i>Какие мои действия действительно соответствовали стоическим ценностям и принципам, а какие шли вразрез с ними?</i>\n"
    "3️⃣ <i>Что из того, что я считал важным на этой неделе, действительно будет иметь значение через год?</i>\n"
    "4️⃣ <i>Какие возможности послужить другим людям я упустил на этой неделе?</i>\n"
    "5️⃣ <i>Какие препятствия и трудности этой недели я смог превратить в возможности для роста, а какие уроки упустил?</i>"
)

async def send_reflection(context: ContextTypes.DEFAULT_TYPE):
    if not subscribers:
        return
    for chat_id in list(subscribers):
        try:
            await context.bot.send_message(chat_id=chat_id, text=REFLECTION_TEXT, parse_mode='HTML')
            logger.info(f"Reflection sent to {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send reflection to {chat_id}: {e}")

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers.add(chat_id)
    text = (
        "✅ Готово! Вы будете получать стоические цитаты каждые 30 секунд.\n"
        "🔔 Убедитесь, что уведомления для этого чата включены, чтобы не пропустить рассылку."
    )
    await update.message.reply_text(text, parse_mode='HTML')
    logger.info(f"Subscribed: {chat_id}")

# Обработчик команды /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        await update.message.reply_text("❌ Вы отписаны от рассылки.")
        logger.info(f"Unsubscribed: {chat_id}")
    else:
        await update.message.reply_text("Вы не были подписаны.")

# Точка входа
if __name__ == '__main__':
    TOKEN = os.getenv('BOT_TOKEN')
    if not TOKEN:
        logger.error('Environment variable BOT_TOKEN is not set')
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('stop', stop))

    # Планировщик задач: цитаты и рефлексия каждые 30 секунд
    job_queue = app.job_queue
    job_queue.run_repeating(send_quote, interval=30, first=0)
    job_queue.run_repeating(send_reflection, interval=30, first=15)

    # Запуск бота
    logger.info('Bot started')
    app.run_polling()
