import os
import logging
import asyncio
from telegram.ext import ApplicationBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def periodic_check(app):
    while True:
        logger.info("Проверка новых объявлений")
        # Здесь логика проверки и рассылки новых объявлений
        await asyncio.sleep(60)  # пауза между проверками

async def on_startup(app):
    app.create_task(periodic_check(app))

def main():
    token = os.getenv("TOKEN")  # читаем именно из переменной TOKEN
    if not token:
        logger.error("Переменная окружения TOKEN не задана!")
        exit(1)

    app = ApplicationBuilder().token(token).build()
    app.post_init = on_startup

    logger.info("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
