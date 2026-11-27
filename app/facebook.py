import re
from html import unescape as html_unescape

import requests

from app.config import GRAPH_TOKEN

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Accept-Language': 'en-US,en;q=0.9'
}

UID_PATTERNS = (r'"pageID":"(\d+)"', r'"target_id":"(\d+)"', r'fb://profile/(\d+)', r'"userID":"(\d+)"')


def fetch_profile_page(username_or_url):
    if "facebook.com" in username_or_url:
        url = username_or_url
    else:
        url = f"https://www.facebook.com/{username_or_url}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        return response.text
    except Exception:
        return None


def extract_uid(html):
    for pattern in UID_PATTERNS:
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    return None


def get_public_uid(username_or_url):
    html = fetch_profile_page(username_or_url)
    if not html:
        return None
    return extract_uid(html)


def get_profile_info(username_or_url):
    html = fetch_profile_page(username_or_url)
    if not html:
        return None

    uid = extract_uid(html)
    if not uid:
        return None

    info = {}

    match = re.search(r'property="og:title" content="([^"]+)"', html)
    if match:
        info["name"] = html_unescape(match.group(1))

    match = re.search(r'"vanity":"([^"]+)"', html)
    if match:
        info["username"] = match.group(1)

    info["UID"] = uid

    match = re.search(r'"is_verified":(true|false)', html)
    if match:
        info["verified"] = match.group(1) == "true"

    match = re.search(r'"category_name":"([^"]+)"', html)
    if match:
        info["category"] = match.group(1)

    match = re.search(r'property="og:description" content="([^"]+)"', html)
    description = html_unescape(match.group(1)) if match else ""

    match = re.search(r'([\d,]+)\s+followers', description) or re.search(r'([\d,]+)\s+followers', html)
    if match:
        info["followers"] = match.group(1)

    match = re.search(r'([\d,]+)\s+following', html)
    if match:
        info["following"] = match.group(1)

    match = re.search(r'([\d,]+)\s+talking about this', description)
    if match:
        info["talking_about"] = match.group(1)

    bio = description
    if info.get("name"):
        bio = re.sub(r'^' + re.escape(info["name"]) + r'\.?\s*', '', bio)
    bio = re.sub(r'[\d,]+\s+followers', '', bio)
    bio = re.sub(r'[\d,]+\s+talking about this', '', bio)
    bio = re.sub(r'\s*·\s*', ' ', bio).strip(' .')
    if len(re.findall(r'[A-Za-z0-9]', bio)) >= 3:
        info["bio"] = bio

    pic = get_profile_pic(uid)
    if pic:
        info["picture"] = pic

    info["profile_url"] = "https://www.facebook.com/" + info.get("username", uid)

    return info


def get_profile_pic(uid):
    try:
        response = requests.get(
            f"https://graph.facebook.com/{uid}/picture",
            params={
                "width": 720,
                "height": 720,
                "access_token": GRAPH_TOKEN,
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
