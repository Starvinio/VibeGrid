from flask import session, redirect
from functools import wraps
import bleach
from datetime import datetime
import re

from app.config import Config


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    
    return wrapper


def allowed_pic(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_IMG_EXTENSIONS

def allowed_audio(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_AUDIO_EXTENSIONS


def process_text(text:str) -> str:
    cleaned_text = bleach.clean(text, tags=Config.ALLOWED_TAGS, strip=True)

    def replace_mention(match):
        username = match.group(1)
        return f'<a style="text-decoration:none" href="/user?u={username}">@{username}</a>'

    mention_pattern = r'@(\w+)'  # @username
    cleaned_text = re.sub(mention_pattern, replace_mention, cleaned_text)

    linked_text = bleach.linkify(cleaned_text)

    text_with_br = linked_text.replace("\n", "<br>")
    text_with_br = text_with_br.replace("fuck", "duck")

    return text_with_br


def darken_hex(hex_color, factor=0.8):
    """Darkens a hex color by a factor (0 < factor < 1)"""
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    darker_rgb = tuple(int(c * factor) for c in rgb)
    return '#{:02x}{:02x}{:02x}'.format(*darker_rgb)


def formatDate(date:datetime):
    currentDate = datetime.now()

    if int(currentDate.year) - int(date.year) > 0 or int(currentDate.month) - int(date.month) > 0 or int(currentDate.day) - int(date.day) > 1:
        return f"{date.day}/{date.month}/{date.year}"
    else:
        day = "Yesterday" if (currentDate.day) - int(date.day) == 1 else "Today"
        return f"{day}, {date.hour}:{date.minute}" if date.minute > 9 else f"{day}, {date.hour}:0{date.minute}"