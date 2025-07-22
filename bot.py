import os
import asyncio
import logging
from typing import Set

import httpx
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# URL с объявлениями, здесь пример — квартиры в Варшаве, можно изменить под свой регион
OTODOM_URL = "https://www.otodom.pl/pl/oferty/sprzedaz/mieszkanie/warszawa"

# Вставь сюда ID чата, куда бот будет рассылать новые объявления
CHAT_ID = int(os.getenv("CHAT_ID", "0"))  # например, "123456789"

# Время между проверками в секундах
CHECK_INTERVAL = 300  # 5 минут

# Хранилище уже отправленных объявлений (по ссылке)
sent_links: Set[str] = set()


async def fetch_listings() -> list[str]:
    """
    Парсим страницу Otodom, возвращаем список ссылок на новые объявления.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Bot/1.0; +https://yourbot.url)"
    }
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(OTODOM_URL, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Селектор ссылок на объявления — может измениться, проверяй актуальность
        offers = soup.select("article > a.css-1bbgabe")  # пример CSS-класса ссылки

        links = []
        for offer in offers:
            href = offer.get("href")
            if href:
                # Ссылки могут быть относительными, добавим домен если нужно
                if href.startswith("/"):
                    href = "https://www.otodom.pl" + href
                links.append(href)

        logger.info(f"Найдено объявлений: {len(links)}")
        return links


async def periodic_check(app: Application):
    while True:
        try:
            logger.info("Проверяем новые объявления на Otodom...")
            new_links = await fetch_listings()

            # Фильтруем только новые ссылки
            fresh = [link for link in new_links if link not in sent_links]

            if not fresh:
                logger.info("Новых объявлений нет.")
            else:
                logger.info(f"Новых объявлений: {len(fresh)}. Отправляем сообщения.")
                for link in fresh:
                    text = f"Новое объявление:\n{link}"
                    await app.bot.send_message(chat_id=CHAT_ID, text=text)
                    sent_links.add(link)

        except Exception as e:
            logger.error(f"Ошибка при проверке объявлений: {e}")

        await asyncio.sleep(CHECK_INTERVAL)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот, буду присылать новые объявления с Otodom.")


async def post_init(app: Application):
    logger.info("Бот запущен. Стартуем периодическую проверку объявлений.")
    app.create_task(periodic_check(app))


def main():
    token = os.getenv("TOKEN")
    if not token:
        logger.error("Переменная окружения TOKEN не установлена. Выход.")
        return
    if CHAT_ID == 0:
        logger.error("Переменная окружения CHAT_ID не установлена или равна 0. Выход.")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.post_init = post_init
    app.run_polling()


if __name__ == "__main__":
    main()
