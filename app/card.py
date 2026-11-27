import io

import requests
from PIL import Image, ImageDraw, ImageFont

from app.config import AUTHOR

FONT_CANDIDATES = [
    ("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ("/data/data/com.termux/files/usr/share/fonts/noto/NotoSans-Regular.ttf", "/data/data/com.termux/files/usr/share/fonts/noto/NotoSans-Bold.ttf"),
    ("/data/data/com.termux/files/usr/share/fonts/dejavu/DejaVuSans.ttf", "/data/data/com.termux/files/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
]

BG = (11, 15, 20)
CARD = (17, 22, 29)
BORDER = (31, 111, 235)
WHITE = (235, 242, 248)
GREY = (139, 152, 165)
LINE = (33, 42, 54)
ACCENT = (47, 129, 247)
GREEN = (46, 204, 113)
RED = (231, 76, 60)


def load_font(size, bold=False):
    for regular, bold_path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(bold_path if bold else regular, size)
        except OSError:
            continue
    return ImageFont.load_default()


def fit_text(draw, text, font, max_width):
    if draw.textlength(text, font=font) <= max_width:
        return text
    while text and draw.textlength(text + "...", font=font) > max_width:
        text = text[:-1]
    return text + "..."


def wrap_text(draw, text, font, max_width, max_lines):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = (current + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
            if len(lines) == max_lines:
                return lines
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines


def load_avatar(info):
    size = 132
    pic = info.get("picture")
    if pic:
        try:
            resp = requests.get(pic, timeout=10)
            img = Image.open(io.BytesIO(resp.content)).convert("RGB")
            w, h = img.size
            side = min(w, h)
            img = img.crop(((w - side) // 2, (h - side) // 2, (w + side) // 2, (h + side) // 2)).resize((size, size))
            mask = Image.new("L", (size, size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
            out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            out.paste(img, (0, 0), mask)
            return out
        except Exception:
            pass
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(out)
    draw.ellipse((0, 0, size, size), fill=(38, 50, 66, 255))
    letter = (info.get("name") or "?").strip()[:1].upper() or "?"
    font = load_font(58, bold=True)
    box = draw.textbbox((0, 0), letter, font=font)
    draw.text(((size - (box[2] - box[0])) / 2 - box[0], (size - (box[3] - box[1])) / 2 - box[1]), letter, font=font, fill=WHITE)
    return out


def make_info_card(info):
    width = 920
    margin = 48
    inner = width - margin * 2

    rows = []
    rows.append(("UID", str(info["UID"])))
    if "verified" in info:
        rows.append(("Verified", "Yes" if info["verified"] else "No"))
    if info.get("category"):
        rows.append(("Category", str(info["category"])))
    if info.get("followers"):
        rows.append(("Followers", str(info["followers"])))
    if info.get("following"):
        rows.append(("Following", str(info["following"])))
    if info.get("talking_about"):
        rows.append(("Talking About", str(info["talking_about"])))

    probe = ImageDraw.Draw(Image.new("RGB", (width, 10)))
    bio_lines = []
    if info.get("bio"):
        bio_lines = wrap_text(probe, str(info["bio"]), load_font(29), inner, 3)

    header_h = 196
    row_h = 62
    bio_h = (44 + len(bio_lines) * 40 + 14) if bio_lines else 0
    footer_h = 84
    height = header_h + len(rows) * row_h + bio_h + footer_h + 30

    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((16, 16, width - 16, height - 16), radius=28, fill=CARD, outline=BORDER, width=2)

    avatar = load_avatar(info)
    img.paste(avatar, (margin, 44), avatar)

    tx = margin + 156
    draw.text((tx, 48), "PROFILE INFORMATION", font=load_font(25, bold=True), fill=ACCENT)
    name = fit_text(draw, str(info.get("name") or info.get("username") or info["UID"]), load_font(42, bold=True), width - tx - margin)
    draw.text((tx, 84), name, font=load_font(42, bold=True), fill=WHITE)
    if info.get("username"):
        draw.text((tx, 138), "@" + str(info["username"]), font=load_font(28), fill=GREY)

    y = header_h
    draw.line((margin, y, width - margin, y), fill=LINE, width=1)
    label_font = load_font(29)
    value_font = load_font(29, bold=True)
    for label, value in rows:
        draw.text((margin, y + 16), label, font=label_font, fill=GREY)
        if label == "Verified":
            dot_color = GREEN if value == "Yes" else RED
            tw = draw.textlength(value, font=value_font)
            draw.ellipse((width - margin - tw - 26, y + 26, width - margin - tw - 10, y + 42), fill=dot_color)
        value = fit_text(draw, value, value_font, inner - 320)
        tw = draw.textlength(value, font=value_font)
        draw.text((width - margin - tw, y + 16), value, font=value_font, fill=WHITE)
        y += row_h
        draw.line((margin, y, width - margin, y), fill=LINE, width=1)

    if bio_lines:
        y += 14
        draw.text((margin, y), "BIO", font=load_font(23, bold=True), fill=ACCENT)
        y += 40
        for line in bio_lines:
            draw.text((margin, y), line, font=load_font(29), fill=WHITE)
            y += 40
        y += 4
        draw.line((margin, y, width - margin, y), fill=LINE, width=1)

    y = height - footer_h + 8
    draw.text((margin, y + 16), str(info["profile_url"]), font=load_font(25), fill=ACCENT)
    author_text = "Author: " + AUTHOR
    tw = draw.textlength(author_text, font=load_font(25, bold=True))
    draw.text((width - margin - tw, y + 16), author_text, font=load_font(25, bold=True), fill=GREY)

    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()
