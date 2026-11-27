import time
from html import escape

import requests

from app.card import make_info_card
from app.config import AUTHOR, BOT_TOKEN
from app.facebook import get_profile_info

API = "https://api.telegram.org/bot" + BOT_TOKEN


def send_message(chat_id, text):
    requests.post(API + "/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}, timeout=15)


def send_photo(chat_id, photo, caption):
    requests.post(API + "/sendPhoto", json={"chat_id": chat_id, "photo": photo, "caption": caption, "parse_mode": "HTML"}, timeout=20)


def send_card(chat_id, card_bytes, caption):
    files = {"photo": ("profile_card.png", card_bytes, "image/png")}
    data = {"chat_id": str(chat_id), "caption": caption, "parse_mode": "HTML"}
    requests.post(API + "/sendPhoto", data=data, files=files, timeout=30)


def format_info(info):
    rows = []
    if info.get("name"):
        rows.append(("Name", str(info["name"])))
    if info.get("username"):
        rows.append(("Username", str(info["username"])))
    rows.append(("UID", str(info["UID"])))
    if "verified" in info:
        rows.append(("Verified", "✅ Yes" if info["verified"] else "❌ No"))
    if info.get("category"):
        rows.append(("Category", str(info["category"])))
    if info.get("followers"):
        rows.append(("Followers", str(info["followers"])))
    if info.get("following"):
        rows.append(("Following", str(info["following"])))
    if info.get("talking_about"):
        rows.append(("Talking", str(info["talking_about"])))
    if info.get("bio"):
        rows.append(("Bio", str(info["bio"])))
    width = max(len(label) for label, _ in rows)
    lines = [escape(label.ljust(width)) + " : " + escape(value) for label, value in rows]
    text = "<b>🔍 PROFILE INFORMATION</b>\n\n<pre>" + "\n".join(lines) + "</pre>"
    text += '\n🔗 <a href="' + escape(str(info["profile_url"])) + '">Open Profile</a>'
    text += "\n\n<b>Author:</b> " + escape(AUTHOR)
    return text


def handle(update):
    msg = update.get("message") or {}
    chat_id = (msg.get("chat") or {}).get("id")
    text = (msg.get("text") or "").strip()
    if not chat_id or not text:
        return
    if text.startswith("/start"):
        send_message(chat_id, "<b>👋 Welcome to R1K4 FB User Hander</b>\n\nSend me a Facebook username or profile link, I will give you the full profile info and picture.\n\n<b>Author:</b> " + escape(AUTHOR))
        return
    ident = text.split()[0]
    info = get_profile_info(ident)
    if not info:
        send_message(chat_id, "❌ <b>Profile not found.</b> The profile might be private or restricted.")
        return
    text_out = format_info(info)
    try:
        card = make_info_card(info)
        caption = "<b>" + escape(str(info.get("name") or info["UID"])) + "</b> — UID <code>" + escape(str(info["UID"])) + "</code>"
        send_card(chat_id, card, caption)
        return
    except Exception:
        pass
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
