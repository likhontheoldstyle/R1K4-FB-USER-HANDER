from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import json
import os
import re
import requests

app = FastAPI(title="USERNAME TO UID")

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

ACCESS_TOKEN = CONFIG.get("graph_token", "")
AUTHOR = CONFIG.get("author", "")
XEFER = CONFIG.get("xefer", "")

def get_public_uid(username_or_url):
    if "facebook.com" in username_or_url:
        url = username_or_url
    else:
        url = f"https://www.facebook.com/{username_or_url}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        html = response.text
        
        page_id_pattern = r'"pageID":"(\d+)"'
        match1 = re.search(page_id_pattern, html)
        if match1: return match1.group(1)
        
        target_id_pattern = r'"target_id":"(\d+)"'
        match2 = re.search(target_id_pattern, html)
        if match2: return match2.group(1)

        meta_pattern = r'fb://profile/(\d+)'
        match3 = re.search(meta_pattern, html)
        if match3: return match3.group(1)

        user_id_pattern = r'"userID":"(\d+)"'
        match4 = re.search(user_id_pattern, html)
        if match4: return match4.group(1)

        return None
            
    except Exception:
        return None

def get_profile_pic(uid):
    try:
        response = requests.get(
            f"https://graph.facebook.com/{uid}/picture",
            params={
                "width": 720,
                "height": 720,
                "access_token": ACCESS_TOKEN,
                "redirect": "false"
            },
            timeout=15
        )
        data = response.json()
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
    except Exception:
        return None

@app.get("/find-uid")
async def find_uid(id: str):
    uid = get_public_uid(id)
    
    if uid:
        return [
            {
                "info": {
                    "status": "success",
                    "username": id,
                    "UID": uid
                }
            },
            {
                "author": AUTHOR,
                "XEFER": XEFER
            }
        ]
    else:
        raise HTTPException(status_code=404, detail="Could not find UID. The profile might be private or restricted.")

@app.get("/profile-pic")
async def profile_pic(id: str, go: int = 0):
    uid = id if id.isdigit() else get_public_uid(id)

    if not uid:
        raise HTTPException(status_code=404, detail="Could not find UID. The profile might be private or restricted.")

    pic = get_profile_pic(uid)

    if not pic:
        raise HTTPException(status_code=404, detail="Could not fetch profile picture.")

    if go == 1:
        return RedirectResponse(pic)

    return [
        {
            "info": {
                "status": "success",
                "username": id,
                "UID": uid,
                "picture": pic
            }
        },
        {
            "author": AUTHOR,
            "XEFER": XEFER
        }
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=CONFIG.get("host", "0.0.0.0"), port=int(CONFIG.get("port", 8000)))
