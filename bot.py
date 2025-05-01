```python
import os
import logging
import random
from datetime import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackContext,
)
from stoic_quotes_100 import QUOTES

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = os.getenv("BOT_TOKEN")

# Хранение подписчиков и их часовых поясов
subscribers = {}  # chat_id -> timezone string

# Отправка цитаты
def quote_job(context: CallbackContext):
    chat_id = context.job.chat_id
    quote = random.choice(QUOTES)
    try:
        context.bot.send_message(chat_id=chat_id, text=quote, parse_mode='HTML')
        logger.info(f"Цитата отправлена: {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке цитаты {chat_id}: {e}")

# Отправка рефлексии
def reflection_job(context: CallbackContext):
    chat_id = context.job.chat_id
    REFLECTION_TEXT = (
        "🧘‍♂️ <b>Стоическая неделя. Время для размышлений.</b>\n"
        "<i>Эти вопросы не для галочки. Найди несколько минут тишины, чтобы честно взглянуть на прожитую неделю.</i>\n\n"
        "1️⃣ В каких ситуациях я позволил эмоциям взять верх над разумом, и как мог бы отреагировать более мудро, мужественно, справедливо и умеренно?\n"
        "2️⃣ Какие мои действия действительно соответствовали стоическим ценностям и принципам, а какие шли вразрез с ними?\n"
        "3️⃣ Что из того, что я считал важным на этой неделе, действительно будет иметь значение через год?\n"
        "4️⃣ Какие возможности послужить другим людям я упустил на этой неделе?\n"
        "5️⃣ Какие препятствия и трудности этой недели я смог превратить в возможности для роста, а какие уроки упустил?"
    )
    try:
        context.bot.send_message(chat_id=chat_id, text=REFLECTION_TEXT, parse_mode='HTML')
        logger.info(f"Рефлексия отправлена: {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке рефлексии {chat_id}: {e}")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # ожидаем, что пользователь указал в контексте свою таймзону
    tz = context.user_data.get('timezone')
    if not tz:
        await update.message.reply_text(
            "Пожалуйста, укажите свой город или часовой пояс командой /setcity перед подпиской."
        )
        return

    # сохраняем подписчика
    subscribers[chat_id] = tz

    # планируем ежедневную цитату в 9:00
    context.job_queue.run_daily(
        quote_job,
        time=time(hour=9, minute=0),
        days=tuple(range(7)),
        context=chat_id,
        name=f"quote_{chat_id}",
        job_kwargs={'timezone': tz}
    )
    # планируем еженедельную рефлексию в воскресенье в 12:00
    context.job_queue.run_weekly(
        reflection_job,
        time=time(hour=12, minute=0),
        days=(6,),  # Sunday
        context=chat_id,
        name=f"reflection_{chat_id}",
        job_kwargs={'timezone': tz}
    )

    await update.message.reply_text(
        "✅ Готово!\n"
        "Теперь Вы будете получать одну мысль из стоицизма каждое утро в 9:00.\n\n"
        "🔔 Убедитесь, что уведомления для этого бота включены, чтобы не пропустить сообщения."
    )
    logger.info(f"Подписан: {chat_id} в TZ {tz}")

# Команда /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        # удаляем задания
        context.job_queue.get_jobs_by_name(f"quote_{chat_id}")[0].schedule_removal()
        context.job_queue.get_jobs_by_name(f"reflection_{chat_id}")[0].schedule_removal()
        subscribers.pop(chat_id, None)
        await update.message.reply_text("❌ Вы отписаны. Подписка отменена.")
        logger.info(f"Отписан: {chat_id}")
    else:
        await update.message.reply_text("Вы не были подписаны.")

# Пример команды установки города/таймзоны
async def setcity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ожидаем текст: название города или TZ, например Europe/Moscow
    text = update.message.text.partition(' ')[2].strip()
    if not text:
        await update.message.reply_text("Использование: /setcity Europe/Moscow")
        return
    # здесь можно добавить валидацию зоны
    context.user_data['timezone'] = text
    await update.message.reply_text(f"Часовой пояс установлен: {text}")
    logger.info(f"TZ для {update.effective_chat.id} = {text}")

# Main
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("setcity", setcity))

    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
```
