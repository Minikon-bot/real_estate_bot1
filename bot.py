import os
import asyncio
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

# URL Otodom и интервал проверки
OTODOM_URL = "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/mazowieckie/warszawa/warszawa/warszawa"
CHECK_INTERVAL = 300  # 5 минут


# Команда /start
async def start(update, context):
    await update.message.reply_text("Привет! Я бот, буду присылать новые объявления с Otodom.")


# Функция получения новых объявлений
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


# Фоновая задача для отправки новых объявлений
async def periodic_task(app: Application, chat_id: int):
    sent_links = set()
    while True:
        try:
            new_listings = await fetch_new_listings(sent_links)
            for link in new_listings - sent_links:
                await app.bot.send_message(chat_id=chat_id, text=f"Новое объявление:\n{link}")
            sent_links |= new_listings
        except Exception as e:
            logger.error(f"Ошибка в периодической задаче: {e}")
        await asyncio.sleep(CHECK_INTERVAL)


# Основная функция запуска бота
def main():
    token = os.getenv("TOKEN")
    chat_id_str = os.getenv("CHAT_ID")
    if not token or not chat_id_str:
        logger.error("Переменные окружения TOKEN и/или CHAT_ID не установлены. Выход.")
        return

    chat_id = int(chat_id_str)

    # Создание приложения Telegram
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))

    # Фоновая задача после старта бота
    async def on_startup(app: Application):
        app.create_task(periodic_task(app, chat_id))

    app.post_init = on_startup

    logger.info("Запускаем бота...")
    app.run_polling(close_loop=False)  # важно: не закрывать цикл событий


if __name__ == "__main__":
    main()
