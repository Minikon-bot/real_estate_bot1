import os
import logging
import asyncio
import json
from datetime import datetime

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackContext,
)

import aiohttp
from bs4 import BeautifulSoup

# Логирование для отладки
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    logger.error("Ошибка: переменная окружения TOKEN не задана")
    exit(1)

SUBSCRIBERS_FILE = "subscribers.json"
SENT_IDS_FILE = "sent_ids.json"

# Сохраняем подписчиков в JSON
def load_subscribers():
    if not os.path.exists(SUBSCRIBERS_FILE):
        return set()
    with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
        return set(json.load(f))

def save_subscribers(subscribers):
    with open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(subscribers), f, ensure_ascii=False)

# Сохраняем уже отправленные ID объявлений
def load_sent_ids():
    if not os.path.exists(SENT_IDS_FILE):
        return set()
    with open(SENT_IDS_FILE, "r", encoding="utf-8") as f:
        return set(json.load(f))

def save_sent_ids(sent_ids):
    with open(SENT_IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(sent_ids), f, ensure_ascii=False)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Это бот для рассылки новых объявлений Otodom.\n"
        "Используй /subscribe чтобы подписаться и получать новые объявления.\n"
        "Используй /unsubscribe чтобы отписаться."
    )

# Команда /subscribe
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    subscribers = load_subscribers()
    if user_id in subscribers:
        await update.message.reply_text("Вы уже подписаны.")
        return
    subscribers.add(user_id)
    save_subscribers(subscribers)
    await update.message.reply_text("Вы подписались на новые объявления!")

# Команда /unsubscribe
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    subscribers = load_subscribers()
    if user_id not in subscribers:
        await update.message.reply_text("Вы не были подписаны.")
        return
    subscribers.remove(user_id)
    save_subscribers(subscribers)
    await update.message.reply_text("Вы отписались от рассылки.")

# Парсим страницу Otodom, получаем новые объявления
async def parse_otodom():
    url = "https://www.otodom.pl/pl/oferty/sprzedaz/mieszkanie/poznan"  # пример для Познани
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Bot/1.0)"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                logger.error(f"Ошибка при загрузке страницы Otodom: {resp.status}")
                return []
            text = await resp.text()
            soup = BeautifulSoup(text, "html.parser")

            # Примерный CSS селектор для объявления на Otodom (надо проверить вручную)
            offers = soup.select("article[data-cy='listing-item']")
            results = []
            for offer in offers:
                # Уникальный ID объявления (можно взять из data-id или из ссылки)
                offer_id = offer.get("data-id")
                if not offer_id:
                    continue
                # Заголовок
                title = offer.select_one("a[data-cy='listing-item-link']").get_text(strip=True)
                # Ссылка
                link = offer.select_one("a[data-cy='listing-item-link']")["href"]
                if not link.startswith("http"):
                    link = "https://www.otodom.pl" + link
                # Цена
                price_tag = offer.select_one("span[data-cy='price']")
                price = price_tag.get_text(strip=True) if price_tag else "цена не указана"
                results.append({
                    "id": offer_id,
                    "title": title,
                    "link": link,
                    "price": price,
                })
            return results

# Функция рассылки новых объявлений подписчикам
async def send_new_offers(app):
    logger.info(f"Запуск проверки новых объявлений {datetime.now()}")
    subscribers = load_subscribers()
    if not subscribers:
        logger.info("Нет подписчиков, пропускаем рассылку")
        return

    sent_ids = load_sent_ids()
    offers = await parse_otodom()
    new_offers = [o for o in offers if o["id"] not in sent_ids]

    if not new_offers:
        logger.info("Новых объявлений нет")
        return

    for offer in new_offers:
        message = f"🏠 {offer['title']}\n💰 {offer['price']}\n🔗 {offer['link']}"
        for user_id in subscribers:
            try:
                await app.bot.send_message(chat_id=user_id, text=message)
            except Exception as e:
                logger.warning(f"Не удалось отправить сообщение {user_id}: {e}")
        sent_ids.add(offer["id"])

    save_sent_ids(sent_ids)
    logger.info(f"Отправлено {len(new_offers)} новых объявлений подписчикам")

# Асинхронная задача для запуска каждые 5 минут
async def periodic_check(app):
    while True:
        try:
            await send_new_offers(app)
        except Exception as e:
            logger.error(f"Ошибка в периодической проверке: {e}")
        await asyncio.sleep(300)  # 5 минут

# Основная функция запуска приложения
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # Запускаем периодическую проверку в фоне
    asyncio.create_task(periodic_check(app))

    logger.info("Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
