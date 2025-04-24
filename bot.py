from telegram import Bot, Update
from telegram.ext import CommandHandler, Updater, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
from stoic_quotes_100 import QUOTES
import random
import os

TOKEN = '7663921238:AAGZaEqkIjvadZE-2hbI2avn6a7asafZM8c'
SUBSCRIBERS_FILE = "subscribers.txt"

def load_subscribers():
    if not os.path.exists(SUBSCRIBERS_FILE):
        return set()
    with open(SUBSCRIBERS_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_subscriber(chat_id):
    subscribers = load_subscribers()
    if str(chat_id) not in subscribers:
        with open(SUBSCRIBERS_FILE, "a") as f:
            f.write(f"{chat_id}\n")
        print(f"Добавлен новый подписчик: {chat_id}")

def remove_subscriber(chat_id):
    subscribers = load_subscribers()
    if str(chat_id) in subscribers:
        subscribers.remove(str(chat_id))
        with open(SUBSCRIBERS_FILE, "w") as f:
            for sub in subscribers:
                f.write(f"{sub}\n")
        print(f"Удалён подписчик: {chat_id}")

def send_quote():
    bot = Bot(token=TOKEN)
    quote = random.choice(QUOTES)
    subscribers = load_subscribers()
    for chat_id in subscribers:
        try:
            bot.send_message(chat_id=chat_id, text=quote)
            print(f"Цитата отправлена {chat_id}: {quote}")
        except Exception as e:
            print(f"Ошибка при отправке в {chat_id}: {e}")

def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    save_subscriber(chat_id)
    context.bot.send_message(chat_id=chat_id, text="✅ Вы подписались на StoicTalesBot. Цитаты будут приходить ежедневно.")

def stop(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    remove_subscriber(chat_id)
    context.bot.send_message(chat_id=chat_id, text="❌ Вы отписались от StoicTalesBot.")

if __name__ == '__main__':
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("stop", stop))

    scheduler = BackgroundScheduler()
    scheduler.add_job(send_quote, 'cron', hour=9, minute=0)
    scheduler.start()

    print("Бот запущен. Ожидает команды и рассылает цитаты.")
    updater.start_polling()
    updater.idle()
