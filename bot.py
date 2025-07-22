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

async def fetch_new_ads():
    url = "https://www.otodom.pl/pl/oferty/sprzedaz/mieszkanie/warszawa"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; TelegramBot/1.0)"
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        html = response.text

    soup = BeautifulSoup(html, "html.parser")
    ads_links = set()

    for a in soup.find_all("a", href=True):
        href = a['href']
        if href.startswith("/oferta/"):
            full_link = "https://www.otodom.pl" + href
            ads_links.add(full_link)

    return list(ads_links)

async def periodic_check(app: Application, chat_id: int):
    while True:
        try:
            logger.info("Проверяем новые объявления...")

            new_ads = await fetch_new_ads()
            fresh_ads = [ad for ad in new_ads if ad not in sent_ads]

            if fresh_ads:
                logger.info(f"Найдено {len(fresh_ads)} новых объявлений.")
                for ad_link in fresh_ads:
                    try:
                        await app.bot.send_message(chat_id=chat_id, text=f"Новое объявление:\n{ad_link}")
                        sent_ads.add(ad_link)
                    except Exception as e:
                        logger.error(f"Ошибка отправки сообщения: {e}")
            else:
                logger.info("Новых объявлений нет.")

        except Exception as e:
            logger.error(f"Ошибка при проверке объявлений: {e}")

        await asyncio.sleep(300)  # Пауза 5 минут

async def main():
    token = os.getenv("TOKEN")
    chat_id_str = os.getenv("CHAT_ID")

    if not token:
        logger.error("Переменная окружения TOKEN не установлена!")
        return
    if not chat_id_str:
        logger.error("Переменная окружения CHAT_ID не установлена!")
        return

    try:
        chat_id = int(chat_id_str)
    except ValueError:
        logger.error("CHAT_ID должен быть числом!")
        return

    app = Application.builder().token(token).build()

    logger.info("Запускаем бота...")

    app.create_task(periodic_check(app, chat_id))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
