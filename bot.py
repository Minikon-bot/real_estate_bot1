import asyncio
import logging
from telegram.ext import ApplicationBuilder

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def periodic_check(app):
    while True:
        logger.info("Запуск проверки новых объявлений")
        subscribers = []  # TODO: заменить на реальных подписчиков
        if not subscribers:
            logger.info("Нет подписчиков, пропускаем рассылку")
        else:
            # TODO: рассылка подписчикам
            pass
        await asyncio.sleep(60)

async def on_startup(app):
    # Создаем задачу после запуска приложения
    app.create_task(periodic_check(app))

def main():
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()

    # Назначаем функцию, вызываемую ПОСЛЕ запуска приложения
    app.post_init = on_startup

    logger.info("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
