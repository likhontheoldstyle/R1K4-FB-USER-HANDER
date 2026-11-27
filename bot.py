import time

import requests

from app.config import AUTHOR, BOT_TOKEN
from app.facebook import get_profile_pic, get_public_uid

API = "https://api.telegram.org/bot" + BOT_TOKEN


def send_message(chat_id, text):
    requests.post(API + "/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=15)


def send_photo(chat_id, photo, caption):
    requests.post(API + "/sendPhoto", json={"chat_id": chat_id, "photo": photo, "caption": caption}, timeout=20)


def handle(update):
    msg = update.get("message") or {}
    chat_id = (msg.get("chat") or {}).get("id")
    text = (msg.get("text") or "").strip()
    if not chat_id or not text:
        return
    if text.startswith("/start"):
        send_message(chat_id, "Send me a Facebook username or profile link, I will give you the UID and profile picture.\n\nAuthor: " + AUTHOR)
        return
    ident = text.split()[0]
    uid = ident if ident.isdigit() else get_public_uid(ident)
    if not uid:
        send_message(chat_id, "UID not found. The profile might be private or restricted.")
        return
    pic = get_profile_pic(uid)
    caption = "Username: " + ident + "\nUID: " + uid
    if pic:
        send_photo(chat_id, pic, caption)
    else:
        send_message(chat_id, caption)


def main():
    offset = 0
    while True:
        try:
            resp = requests.get(API + "/getUpdates", params={"offset": offset, "timeout": 30}, timeout=40)
            data = resp.json()
            for update in data.get("result", []):
                offset = update["update_id"] + 1
                handle(update)
        except Exception:
            time.sleep(3)


if __name__ == "__main__":
    main()
