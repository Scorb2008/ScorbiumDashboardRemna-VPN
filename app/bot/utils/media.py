"""
Утилиты для отправки и редактирования сообщений.
Корректно обрабатывает сообщения с фото (caption) и без (text).
"""

from typing import Optional
import base64

from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    BufferedInputFile,
)
from aiogram.exceptions import TelegramBadRequest


def _safe_answer_callback(callback: CallbackQuery) -> None:
    """Sync helper — nothing. Answer is async, use _safe_answer_cb."""
    pass


async def _safe_answer_cb(callback: CallbackQuery) -> None:
    """Безопасно отвечаем на callback query — игнорируем все ошибки."""
    try:
        await callback.answer()
    except Exception:
        pass


async def safe_answer_cb(
    callback: CallbackQuery, text: str = "", show_alert: bool = False
) -> None:
    """Безопасно отвечаем на callback query с текстом/алертом."""
    try:
        await callback.answer(text[:200] if text else "", show_alert=show_alert)
    except Exception:
        pass


def resolve_photo_input(photo: Optional[str]) -> Optional[str | BufferedInputFile]:
    if not photo:
        return None

    value = str(photo).strip()
    if not value:
        return None

    payload = value
    if value.startswith("data:image/") and "," in value:
        payload = value.split(",", 1)[1].strip()

    try:
        decoded = base64.b64decode(payload, validate=True)
    except Exception:
        return value

    image_signatures = (
        b"\xff\xd8\xff",
        b"\x89PNG\r\n\x1a\n",
        b"GIF87a",
        b"GIF89a",
        b"RIFF",
    )
    if not decoded.startswith(image_signatures):
        return value

    extension = "jpg"
    if decoded.startswith(b"\x89PNG\r\n\x1a\n"):
        extension = "png"
    elif decoded.startswith((b"GIF87a", b"GIF89a")):
        extension = "gif"
    elif decoded.startswith(b"RIFF") and decoded[8:12] == b"WEBP":
        extension = "webp"

    return BufferedInputFile(decoded, filename=f"bot_photo.{extension}")


async def answer_with_photo(
    message: Message,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    photo: Optional[str] = None,
    parse_mode: str = "HTML",
) -> Optional[Message]:
    """Отправляет новое сообщение — с фото если есть file_id, иначе текст."""
    photo_input = resolve_photo_input(photo)
    if photo_input:
        try:
            return await message.answer_photo(
                photo=photo_input,
                caption=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
        except TelegramBadRequest:
            pass
        try:
            return await message.answer_photo(
                photo=photo_input,
                caption=text,
                reply_markup=reply_markup,
            )
        except TelegramBadRequest:
            pass
    try:
        return await message.answer(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    except TelegramBadRequest:
        pass
    return await message.answer(
        text=text,
        reply_markup=reply_markup,
    )


async def edit_with_photo(
    callback: CallbackQuery,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    photo: Optional[str] = None,
    parse_mode: str = "HTML",
) -> None:
    """
    Редактирует текущее сообщение или отправляет новое.
    Безопасно обрабатывает все ошибки Telegram API.
    """
    msg = callback.message
    if msg is None:
        return

    chat = msg.chat
    if chat is None:
        return

    photo_input = resolve_photo_input(photo)
    if photo_input:
        try:
            await msg.delete()
        except Exception:
            pass
        try:
            await chat.send_message(
                text=text, reply_markup=reply_markup, parse_mode=parse_mode
            )
            return
        except TelegramBadRequest:
            pass
        try:
            await chat.send_message(
                text=text, reply_markup=reply_markup
            )
        except Exception:
            pass
        return

    try:
        await msg.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        return
    except TelegramBadRequest as e:
        err = str(e)
        if "message is not modified" in err:
            return
        if "there is no text in the message" in err:
            try:
                await msg.edit_caption(
                    caption=text, reply_markup=reply_markup, parse_mode=parse_mode
                )
                return
            except Exception:
                pass
        if "message to edit not found" in err or "message can't be edited" in err:
            try:
                await chat.send_message(
                    text=text, reply_markup=reply_markup, parse_mode=parse_mode
                )
            except TelegramBadRequest:
                try:
                    await chat.send_message(
                        text=text, reply_markup=reply_markup
                    )
                except Exception:
                    pass
            except Exception:
                pass
            return
    except Exception:
        pass

    try:
        await msg.delete()
    except Exception:
        pass
    try:
        await chat.send_message(
            text=text, reply_markup=reply_markup, parse_mode=parse_mode
        )
    except TelegramBadRequest:
        try:
            await chat.send_message(
                text=text, reply_markup=reply_markup
            )
        except Exception:
            pass
    except Exception:
        pass


async def safe_edit(
    callback: CallbackQuery,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: str = "HTML",
) -> None:
    """Безопасное редактирование без фото — обрабатывает caption и text."""
    await edit_with_photo(
        callback, text, reply_markup=reply_markup, parse_mode=parse_mode
    )
