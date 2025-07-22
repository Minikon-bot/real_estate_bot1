import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Логирование для отладки
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("TOKEN")  # Токен бота берём из переменной окружения

if not TOKEN:
    raise RuntimeError("❌ Ошибка: переменная окружения TOKEN не задана! Добавьте её в Render → Environment Variables.")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Бот успешно запущен на python-telegram-bot 20.3!")

# Основная функция запуска
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрируем хендлеры
    app.add_handler(CommandHandler("start", start))

    logging.info("Бот запущен и ожидает сообщения...")
    app.run_polling()

if __name__ == "__main__":
    main()
