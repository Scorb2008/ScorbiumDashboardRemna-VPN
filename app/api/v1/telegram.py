from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile, status
from pydantic import BaseModel
from typing import Optional

from app.api.dependencies import get_current_admin
from app.services.telegram_notify import TelegramNotifyService


def _get_bot():
    """Lazy import to avoid circular import at module level."""
    from app.core.server import get_bot as _gb
    return _gb()


router = APIRouter()


class DirectMessageBody(BaseModel):
    chat_id: int
    text: str
    parse_mode: str = "HTML"


class SetNameBody(BaseModel):
    name: str
    language_code: str = "ru"


class SetDescriptionBody(BaseModel):
    description: str
    short_description: str = ""
    language_code: str = "ru"


class SetCommandsBody(BaseModel):
    commands: list[dict]


@router.get("/bot-info", summary="Get Telegram bot info")
async def bot_info(_: str = Depends(get_current_admin)) -> dict:
    notify = TelegramNotifyService()
    info = await notify.get_bot_info()
    if not info:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to reach Telegram API",
        )
    return info


@router.post("/send", summary="Send direct message via bot")
async def send_direct(
    body: DirectMessageBody,
    _: str = Depends(get_current_admin),
) -> dict:
    notify = TelegramNotifyService()
    ok = await notify.send_message(body.chat_id, body.text, body.parse_mode)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to send message"
        )
    return {"detail": "sent"}


@router.post("/set-name", summary="Set bot name")
async def set_bot_name(
    body: SetNameBody,
    _: str = Depends(get_current_admin),
) -> dict:
    bot = _get_bot()
    try:
        await bot.set_my_name(name=body.name, language_code=body.language_code)
        return {"ok": True, "detail": f"Bot name set to '{body.name}'"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/set-description", summary="Set bot description & short description")
async def set_bot_description(
    body: SetDescriptionBody,
    _: str = Depends(get_current_admin),
) -> dict:
    bot = _get_bot()
    try:
        await bot.set_my_description(
            description=body.description, language_code=body.language_code
        )
        if body.short_description:
            await bot.set_my_short_description(
                short_description=body.short_description,
                language_code=body.language_code,
            )
        return {"ok": True, "detail": "Bot description updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/set-photo", summary="Upload bot photo")
async def set_bot_photo(
    file: UploadFile = File(...),
    _: str = Depends(get_current_admin),
) -> dict:
    bot = _get_bot()
    try:
        contents = await file.read()
        from aiogram.types import BufferedInputFile

        photo = BufferedInputFile(file=contents, filename=file.filename or "bot.png")
        await bot.set_my_photo(photo=photo)
        return {"ok": True, "detail": "Bot photo updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/delete-photo", summary="Delete bot photo")
async def delete_bot_photo(
    _: str = Depends(get_current_admin),
) -> dict:
    bot = _get_bot()
    try:
        await bot.delete_my_photo()
        return {"ok": True, "detail": "Bot photo deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/set-commands", summary="Set bot commands")
async def set_bot_commands(
    body: SetCommandsBody,
    _: str = Depends(get_current_admin),
) -> dict:
    bot = _get_bot()
    try:
        from aiogram.types import BotCommand

        commands = [BotCommand(**c) for c in body.commands]
        await bot.set_my_commands(commands=commands)
        return {"ok": True, "detail": f"{len(commands)} commands set"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/get-commands", summary="Get current bot commands")
async def get_bot_commands(
    _: str = Depends(get_current_admin),
) -> list[dict]:
    bot = _get_bot()
    try:
        cmds = await bot.get_my_commands()
        return [{"command": c.command, "description": c.description} for c in cmds]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/get-name", summary="Get bot name")
async def get_bot_name(
    language_code: str = "ru",
    _: str = Depends(get_current_admin),
) -> dict:
    bot = _get_bot()
    try:
        name = await bot.get_my_name(language_code=language_code)
        return {"name": name.name if name else "", "language_code": language_code}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/get-description", summary="Get bot description")
async def get_bot_description(
    language_code: str = "ru",
    _: str = Depends(get_current_admin),
) -> dict:
    bot = _get_bot()
    try:
        desc = await bot.get_my_description(language_code=language_code)
        short = await bot.get_my_short_description(language_code=language_code)
        return {
            "description": desc.description if desc else "",
            "short_description": short.short_description if short else "",
            "language_code": language_code,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refresh-webhook", summary="Re-set Telegram webhook")
async def refresh_webhook(
    _: str = Depends(get_current_admin),
) -> dict:
    from app.core.config import config

    bot = _get_bot()
    try:
        webhook_url = config.telegram.telegram_webhook_url
        if webhook_url:
            await bot.set_webhook(url=webhook_url)
            return {"ok": True, "detail": f"Webhook set to {webhook_url}"}
        else:
            await bot.delete_webhook()
            return {"ok": True, "detail": "Webhook deleted (polling mode)"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
