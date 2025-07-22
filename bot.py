import os
import sys
from telegram import Bot
from telegram.ext import Updater, CommandHandler

# Получаем токен из переменной окружения
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    sys.exit("❌ Ошибка: переменная окружения TOKEN не задана. "
             "Добавьте её в настройках Render → Environment Variables.")

# Инициализация бота
bot = Bot(token=TOKEN)
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Пример команды /start
def start(update, context):
    update.message.reply_text("Бот запущен и работает!")

dispatcher.add_handler(CommandHandler("start", start))

# Запуск бота
if __name__ == "__main__":
    print("Бот успешно запущен...")
    updater.start_polling()
    updater.idle()
