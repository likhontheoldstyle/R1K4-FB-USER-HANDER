import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

BOT_TOKEN = CONFIG.get("bot_token", "")
ADMIN_UID = CONFIG.get("admin_uid", "")
GRAPH_TOKEN = CONFIG.get("graph_token", "")
AUTHOR = CONFIG.get("author", "")
HOST = CONFIG.get("host", "0.0.0.0")
PORT = int(CONFIG.get("port", 8000))
