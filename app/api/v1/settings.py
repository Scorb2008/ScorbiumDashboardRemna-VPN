"""REST API endpoints for settings and configuration."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_admin
from app.core.config import config
from app.services.bot_settings import BotSettingsService

router = APIRouter()


@router.get("/")
async def get_settings(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    svc = BotSettingsService(db)
    settings = await svc.get_all()
    return settings


@router.patch("/")
async def update_settings(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    svc = BotSettingsService(db)
    await svc.set_many(body)
    await db.commit()
    return {"ok": True}


@router.get("/payment-systems")
async def get_payment_systems(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    svc = BotSettingsService(db)
    settings = await svc.get_all()
    systems = {}
    for key in settings:
        if key.startswith("payment_system_"):
            name = key.replace("payment_system_", "")
            systems[name] = settings[key]
    return systems


@router.get("/config")
async def get_config(
    _admin=Depends(get_current_admin),
):
    return {
        "app_name": config.web.app_name,
        "app_version": config.web.app_version,
        "site_url": config.web.site_url,
        "domain": config.web.domain,
        "panel_path": config.web.set_path_admin,
        "bot_username": config.telegram.telegram_bot_username,
        "has_yookassa": bool(config.yookassa.yookassa_shop_id),
        "has_remnawave": bool(
            config.remnawave.remnawave_admin_panel
            and (config.remnawave.has_password_auth or config.remnawave.has_api_key)
        ),
    }
