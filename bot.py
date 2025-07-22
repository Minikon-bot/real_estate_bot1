import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    logger.error("❌ Ошибка: переменная окружения TOKEN не задана.")
    exit(1)

subscribers = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Бот успешно запущен на python-telegram-bot 20.3!")

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

async def periodic_check(app):
    while True:
        logger.info("Запуск проверки новых объявлений")
        if not subscribers:
            logger.info("Нет подписчиков, пропускаем рассылку")
        else:
            new_listings = ["Новое объявление 1", "Новое объявление 2"]
            for chat_id in subscribers:
                for listing in new_listings:
                    try:
                        await app.bot.send_message(chat_id=chat_id, text=listing)
                    except Exception as e:
                        logger.error(f"Ошибка при отправке сообщения {chat_id}: {e}")
        await asyncio.sleep(60)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # Запускаем фоновую задачу
    app.create_task(periodic_check(app))

    logger.info("Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    # Важно: запускаем main() через asyncio.run() **только если у вас нет уже запущенного event loop**
    # В Render-среде часто loop уже есть, поэтому запускаем так:

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Если loop уже запущен — запускаем main() как таску
        loop.create_task(main())
        # И удерживаем process живым
        loop.run_forever()
    else:
        # Если loop нет — безопасно запускаем
        asyncio.run(main())
