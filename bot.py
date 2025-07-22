import os
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот.")

async def periodic_check(app: Application):
    while True:
        logger.info("Запуск проверки новых объявлений")
        # Здесь твоя логика проверки и рассылки
        # Например, проверка базы, отправка сообщений подписчикам и т.п.
        await asyncio.sleep(60)  # Пауза 60 секунд между проверками

async def post_init(app: Application):
    logger.info("Бот запущен")
    app.create_task(periodic_check(app))

def main():
    token = os.getenv("TOKEN")
    if not token:
        logger.error("Переменная окружения TOKEN не установлена. Выход.")
        return

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.post_init = post_init  # Запуск периодической задачи после старта

    app.run_polling()

if __name__ == "__main__":
    main()
