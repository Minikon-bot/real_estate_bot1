import asyncio
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Токен из переменной окружения
import os
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    logger.error("❌ Ошибка: переменная окружения TOKEN не задана.")
    exit(1)

# Пример командного обработчика /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Бот успешно запущен на python-telegram-bot 20.3!")

# Пример подписки (подписчики хранятся в памяти, для примера)
subscribers = set()

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in subscribers:
        subscribers.add(chat_id)
        await update.message.reply_text("Вы подписались на новые объявления.")
        logger.info(f"Новый подписчик: {chat_id}")
    else:
        await update.message.reply_text("Вы уже подписаны.")

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        await update.message.reply_text("Вы отписались от новых объявлений.")
        logger.info(f"Отписался: {chat_id}")
    else:
        await update.message.reply_text("Вы не были подписаны.")

# Пример фоновой задачи, которая периодически проверяет новые объявления
async def periodic_check(app):
    while True:
        logger.info("Запуск проверки новых объявлений")
        if not subscribers:
            logger.info("Нет подписчиков, пропускаем рассылку")
        else:
            # Здесь логика получения новых объявлений (замените на свою)
            new_listings = ["Новое объявление 1", "Новое объявление 2"]  # пример

            for chat_id in subscribers:
                for listing in new_listings:
                    try:
                        await app.bot.send_message(chat_id=chat_id, text=listing)
                    except Exception as e:
                        logger.error(f"Ошибка при отправке сообщения {chat_id}: {e}")

        await asyncio.sleep(60)  # Проверять раз в минуту

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрируем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # Запускаем фоновую задачу
    asyncio.create_task(periodic_check(app))

    logger.info("Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
