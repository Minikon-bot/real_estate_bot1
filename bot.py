import os
import asyncio
import logging
from typing import Set

import httpx
from bs4 import BeautifulSoup

from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

OTODOM_URL = "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/mazowieckie/warszawa/warszawa/warszawa"
CHECK_INTERVAL = 300  # 5 минут


async def start(update: ContextTypes.DEFAULT_TYPE, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот, буду присылать новые объявления с Otodom.")


async def fetch_new_listings(existing_links: Set[str]) -> Set[str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Bot/1.0; +https://github.com/)"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(OTODOM_URL, headers=headers, follow_redirects=True)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        ads = soup.select("a.css-1bbgabe")

        new_links = set()
        for a in ads:
            href = a.get("href")
            if href and href.startswith("https://www.otodom.pl/oferta/"):
                if href not in existing_links:
                    new_links.add(href)

        return new_links


async def periodic_task(app: Application, chat_id: int):
    logger.info("Старт периодической проверки новых объявлений")
    sent_links = set()

    while True:
        try:
            logger.info("Проверяем новые объявления на Otodom...")
            new_listings = await fetch_new_listings(sent_links)

            if new_listings:
                logger.info(f"Найдено новых объявлений: {len(new_listings)}")
                for link in new_listings:
                    await app.bot.send_message(chat_id=chat_id, text=f"Новое объявление:\n{link}")
                    sent_links.add(link)
            else:
                logger.info("Новых объявлений нет.")

        except Exception as e:
            logger.error(f"Ошибка при проверке объявлений: {e}")

        await asyncio.sleep(CHECK_INTERVAL)


async def main():
    token = os.getenv("TOKEN")
    chat_id_str = os.getenv("CHAT_ID")

    if not token or not chat_id_str:
        logger.error("Переменные окружения TOKEN и/или CHAT_ID не установлены. Выход.")
        return

    try:
        chat_id = int(chat_id_str)
    except Exception:
        logger.error("CHAT_ID должен быть целым числом.")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))

    async def on_startup(app: Application):
        app.create_task(periodic_task(app, chat_id))

    app.post_init = on_startup

    logger.info("Запускаем бота...")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
