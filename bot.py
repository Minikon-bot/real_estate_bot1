import os
import logging
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import json

# --- Конфигурация ---
CHECK_INTERVAL = 60  # проверка новых объявлений каждые 60 секунд
SENT_LINKS_FILE = "sent_links.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Функции для работы с файлами ---
def load_sent_links():
    if os.path.exists(SENT_LINKS_FILE):
        try:
            with open(SENT_LINKS_FILE, "r") as f:
                return set(json.load(f))
        except Exception as e:
            logger.error(f"Ошибка загрузки файла sent_links.json: {e}")
    return set()

def save_sent_links(sent_links):
    try:
        with open(SENT_LINKS_FILE, "w") as f:
            json.dump(list(sent_links), f)
    except Exception as e:
        logger.error(f"Ошибка сохранения файла sent_links.json: {e}")

# --- Парсинг Otodom ---
async def fetch_new_listings():
    url = "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/mazowieckie/warszawa/warszawa/warszawa"
    listings = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")
                for link in soup.select("a[data-cy='listing-item-link']"):
                    href = link.get("href")
                    if href and href.startswith("http"):
                        listings.append(href)
    except Exception as e:
        logger.error(f"Ошибка парсинга Otodom: {e}")
    return listings

# --- JobQueue задача ---
async def job_send_new_listings(context: ContextTypes.DEFAULT_TYPE):
    chat_id = os.getenv("CHAT_ID")
    if not chat_id:
        logger.error("CHAT_ID не установлен в переменных окружения")
        return

    sent_links = context.job.data["sent_links"]
    new_links = await fetch_new_listings()
    new_items = [link for link in new_links if link not in sent_links]

    if new_items:
        for link in new_items:
            try:
                await context.bot.send_message(chat_id=chat_id, text=f"Новое объявление: {link}")
                sent_links.add(link)
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения: {e}")
        save_sent_links(sent_links)

# --- Команда /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен. Буду присылать новые объявления с Otodom!")

# --- Основной запуск ---
def main():
    token = os.getenv("TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not token or not chat_id:
        logger.error("Переменные окружения TOKEN и/или CHAT_ID не установлены.")
        return

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))

    # Загружаем отправленные ссылки
    sent_links = load_sent_links()

    if app.job_queue:
        app.job_queue.run_repeating(job_send_new_listings, interval=CHECK_INTERVAL, first=5, data={"sent_links": sent_links})
    else:
        logger.error("JobQueue не активирован. Установите python-telegram-bot[job-queue].")

    logger.info("Запускаем бота...")
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
