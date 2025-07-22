import os
import json
import logging
from typing import Set

import httpx
from bs4 import BeautifulSoup
from telegram.ext import Application, CommandHandler

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Конфигурация
OTODOM_URL = "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/mazowieckie/warszawa/warszawa/warszawa"
CHECK_INTERVAL = 300  # 5 минут
STATE_FILE = "sent_links.json"


def load_sent_links() -> Set[str]:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return set(json.load(f))
        except Exception as e:
            logger.error(f"Ошибка при загрузке {STATE_FILE}: {e}")
    return set()


def save_sent_links(sent_links: Set[str]):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(list(sent_links), f)
    except Exception as e:
        logger.error(f"Ошибка при сохранении {STATE_FILE}: {e}")


async def start(update, context):
    await update.message.reply_text("Привет! Я бот и буду присылать новые объявления с Otodom.")


async def fetch_new_listings(existing_links: Set[str]) -> Set[str]:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Bot/1.0; +https://github.com/)"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(OTODOM_URL, headers=headers, follow_redirects=True, timeout=15.0)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            ads = soup.select("a.css-1bbgabe")
            return {a.get("href") for a in ads if a.get("href", "").startswith("https://www.otodom.pl/oferta/")}
    except Exception as e:
        logger.error(f"Ошибка при загрузке объявлений: {e}")
        return set()


async def job_send_new_listings(context):
    app = context.application
    chat_id = int(os.getenv("CHAT_ID"))
    sent_links = context.job.data.setdefault("sent_links", load_sent_links())
    new_listings = await fetch_new_listings(sent_links)
    new_to_send = new_listings - sent_links

    for link in new_to_send:
        await app.bot.send_message(chat_id=chat_id, text=f"Новое объявление:\n{link}")

    if new_to_send:
        sent_links |= new_to_send
        save_sent_links(sent_links)


def main():
    token = os.getenv("TOKEN")
    chat_id = os.getenv("CHAT_ID")
    if not token or not chat_id:
        logger.error("Переменные окружения TOKEN и/или CHAT_ID не установлены.")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))

    # Загружаем уже отправленные ссылки
    sent_links = load_sent_links()
    app.job_queue.run_repeating(job_send_new_listings, interval=CHECK_INTERVAL, first=5, data={"sent_links": sent_links})

    logger.info("Запускаем бота...")
    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
