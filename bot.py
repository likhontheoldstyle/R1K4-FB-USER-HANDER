import time

import requests

from app.config import AUTHOR, BOT_TOKEN
from app.facebook import get_profile_info

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
        send_message(chat_id, "Send me a Facebook username or profile link, I will give you the full profile info and picture.\n\nAuthor: " + AUTHOR)
        return
    ident = text.split()[0]
    info = get_profile_info(ident)
    if not info:
        send_message(chat_id, "Profile not found. The profile might be private or restricted.")
        return
    lines = []
    if info.get("name"):
        lines.append("Name: " + str(info["name"]))
    if info.get("username"):
        lines.append("Username: " + str(info["username"]))
    lines.append("UID: " + str(info["UID"]))
    if "verified" in info:
        lines.append("Verified: " + ("Yes" if info["verified"] else "No"))
    if info.get("category"):
        lines.append("Category: " + str(info["category"]))
    if info.get("followers"):
        lines.append("Followers: " + str(info["followers"]))
    if info.get("following"):
        lines.append("Following: " + str(info["following"]))
    if info.get("talking_about"):
        lines.append("Talking about: " + str(info["talking_about"]))
    if info.get("bio"):
        lines.append("Bio: " + str(info["bio"]))
    lines.append("Profile: " + str(info["profile_url"]))
    text_out = "\n".join(lines)
    if info.get("picture"):
        send_photo(chat_id, info["picture"], text_out)
    else:
        send_message(chat_id, text_out)


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
