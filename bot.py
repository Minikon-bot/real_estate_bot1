import os
import json
import time
import threading
import requests
from flask import Flask, request
from bs4 import BeautifulSoup
from telegram import Bot

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL") + "/webhook"

bot = Bot(token=TOKEN)
app = Flask(__name__)

SUBSCRIBERS_FILE = "subscribers.json"
SENT_ADS_FILE = "sent_ads.json"
OTODOM_URL = "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie,poznan"  # пример страницы

# --- Helpers ---
def load_json(file):
    if not os.path.exists(file):
        return []
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def parse_otodom():
    """Парсинг объявлений с Otodom"""
    resp = requests.get(OTODOM_URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "html.parser")
    ads = []
    for ad in soup.select("article a[data-cy='listing-item-link']"):
        link = ad.get("href")
        if link:
            ads.append(link)
    return ads

def send_new_ads():
    """Фоновая задача — проверка каждые 5 минут"""
    while True:
        try:
            sent_ads = load_json(SENT_ADS_FILE)
            subscribers = load_json(SUBSCRIBERS_FILE)
            new_ads = parse_otodom()

            for ad in new_ads:
                if ad not in sent_ads:
                    for user in subscribers:
                        bot.send_message(chat_id=user, text=f"Новое объявление: {ad}")
                    sent_ads.append(ad)

            save_json(SENT_ADS_FILE, sent_ads)
        except Exception as e:
            print("Ошибка парсинга:", e)
        time.sleep(300)

# --- Flask routes ---
@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json()
    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"]

        if text == "/start":
            subscribers = load_json(SUBSCRIBERS_FILE)
            if chat_id not in subscribers:
                subscribers.append(chat_id)
                save_json(SUBSCRIBERS_FILE, subscribers)
            bot.send_message(chat_id, "Вы подписаны на уведомления!")
    return "ok", 200

@app.route("/")
def index():
    return "Бот работает!", 200

# --- Webhook setup ---
def set_webhook():
    bot.delete_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    set_webhook()
    threading.Thread(target=send_new_ads, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
