from typing import Optional
from aiogram.types import InlineKeyboardButton, WebAppInfo


def btn(
    text: str,
    callback_data: str = None,
    url: str = None,
    web_app: str = None,
    style: Optional[str] = None,
    emoji_id: Optional[str] = None,
) -> InlineKeyboardButton:
    kwargs: dict = {"text": text}
    if callback_data:
        kwargs["callback_data"] = callback_data
    if url:
        kwargs["url"] = url
    if web_app:
        kwargs["web_app"] = WebAppInfo(url=web_app)
    if style in ("primary", "secondary"):
        kwargs["style"] = style
    if emoji_id and emoji_id.strip().isdigit():
        kwargs["icon_custom_emoji_id"] = emoji_id.strip()
    try:
        return InlineKeyboardButton(**kwargs)
    except Exception:
        for k in ("style", "icon_custom_emoji_id"):
            kwargs.pop(k, None)
        return InlineKeyboardButton(**kwargs)
