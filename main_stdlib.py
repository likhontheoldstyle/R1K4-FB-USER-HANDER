import json
import os
import re
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "token.txt")


def load_token():
    token = os.environ.get("FB_ACCESS_TOKEN", "").strip()
    if token:
        return token
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            token = f.read().strip()
        if token:
            return token
    except OSError:
        pass
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py"), "r", encoding="utf-8") as f:
            match = re.search(r'ACCESS_TOKEN\s*=\s*"([^"]+)"', f.read())
        if match:
            return match.group(1).strip()
    except OSError:
        pass
    return ""


ACCESS_TOKEN = load_token()


def get_public_uid(username_or_url):
    if "facebook.com" in username_or_url:
        url = username_or_url
    else:
        url = "https://www.facebook.com/" + username_or_url
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", "ignore")
    except Exception:
        return None
    for pattern in (r'"pageID":"(\d+)"', r'"target_id":"(\d+)"', r'fb://profile/(\d+)', r'"userID":"(\d+)"'):
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    return None


def get_profile_pic(uid):
    if not ACCESS_TOKEN:
        return None
    params = urllib.parse.urlencode({
        "width": 720,
        "height": 720,
        "access_token": ACCESS_TOKEN,
        "redirect": "false",
    })
    req = urllib.request.Request("https://graph.facebook.com/" + uid + "/picture?" + params, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8", "ignore"))
    except Exception:
        return None
    if isinstance(data, str):
        pic = data
    else:
        info = data.get("data") or {}
        if info.get("is_silhouette"):
            return None
        pic = info.get("url")
    if pic and "t1.30497-1" not in pic:
        return pic
    return None


def author_block():
    return {"author": "LIKHON AHMED", "XEFER": "HIMU"}


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        ident = (query.get("id") or [""])[0]
        if parsed.path == "/find-uid":
            uid = get_public_uid(ident)
            if uid:
                self.send_json(200, [
                    {"info": {"status": "success", "username": ident, "UID": uid}},
                    author_block(),
                ])
            else:
                self.send_json(404, {"detail": "Could not find UID. The profile might be private or restricted."})
            return
        if parsed.path == "/profile-pic":
            uid = ident if ident.isdigit() else get_public_uid(ident)
            if not uid:
                self.send_json(404, {"detail": "Could not find UID. The profile might be private or restricted."})
                return
            if not ACCESS_TOKEN:
                self.send_json(404, {"detail": "FB_ACCESS_TOKEN not set. Set it with export FB_ACCESS_TOKEN=... or put it in token.txt"})
                return
            pic = get_profile_pic(uid)
            if not pic:
                self.send_json(404, {"detail": "Could not fetch profile picture."})
                return
            if (query.get("go") or ["0"])[0] == "1":
                self.send_response(302)
                self.send_header("Location", pic)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_json(200, [
                {"info": {"status": "success", "username": ident, "UID": uid, "picture": pic}},
                author_block(),
            ])
            return
        self.send_json(200, {"status": "ok", "usage": "/find-uid?id=USERNAME | /profile-pic?id=USERNAME&go=1"})

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
