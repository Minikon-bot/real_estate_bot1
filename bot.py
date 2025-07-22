import os
import asyncio
import logging
import httpx
from bs4 import BeautifulSoup
from telegram.ext import Application

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

sent_ads = set()

async def fetch_ads():
    url = "https://www.otodom.pl/pl/oferty/sprzedaz/mieszkanie/warszawa"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "html.parser")

    ads = set()
    # В Otodom ссылки на объявления обычно в тегах <a> с href, содержащим "/oferta/"
    for a in soup.find_all("a", href=True):
        href = a['href']
        if href.startswith("/oferta/"):
            full_link = "https://www.otodom.pl" + href
            ads.add(full_link)
    return ads

async def send_new_ads(app: Application, chat_id: int):
    global sent_ads
    try:
        ads = await fetch_ads()
        new_ads = ads - sent_ads
        if new_ads:
            logger.info(f"Найдено {len(new_ads)} новых объявлений.")
            for link in new_ads:
                try:
                    await app.bot.send_message(chat_id=chat_id, text=f"Новое объявление:\n{link}")
                    sent_ads.add(link)
                except Exception as e:
                    logger.error(f"Ошибка отправки сообщения: {e}")
        else:
            logger.info("Новых объявлений нет.")
    except Exception as e:
        logger.error(f"Ошибка при парсинге или отправке: {e}")

async def periodic_task(app: Application, chat_id: int):
    while True:
        await send_new_ads(app, chat_id)
        await asyncio.sleep(300)  # Проверяем каждые 5 минут

async def main():
    token = os.getenv("TOKEN")
    chat_id_str = os.getenv("CHAT_ID")

    if not token:
        logger.error("Не задана переменная окружения TOKEN")
        return
    if not chat_id_str:
        logger.error("Не задана переменная окружения CHAT_ID")
        return

    try:
        chat_id = int(chat_id_str)
    except ValueError:
        logger.error("CHAT_ID должен быть числом")
        return

    app = Application.builder().token(token).build()

    logger.info("Запускаем бота...")

    app.create_task(periodic_task(app, chat_id))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
