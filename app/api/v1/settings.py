"""REST API endpoints for settings and configuration."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.api.dependencies import get_db, get_current_admin
from app.core.config import config
from app.services.bot_settings import BotSettingsService

router = APIRouter()

_SENSITIVE_KEYS = frozenset({
    "yookassa_secret_key_override",
    "cryptobot_token",
    "freekassa_api_key",
    "freekassa_secret_word_1",
    "freekassa_secret_word_2",
    "aikassa_token",
    "platega_secret",
    "paypalych_api_token",
})

_ALLOWED_SETTINGS_KEYS = frozenset({
    "welcome_message", "ban_message", "bot_disabled_message",
    "btn_order", "keyboard_layout",
    "btn_buy", "btn_my_keys", "btn_status",
    "btn_payments", "btn_profile", "btn_support", "btn_language", "btn_trial",
    "btn_gift", "btn_extend", "btn_balance", "btn_language_label",
    "btn_buy_label", "btn_my_keys_label", "btn_status_label",
    "btn_payments_label", "btn_profile_label", "btn_support_label",
    "btn_trial_label", "btn_gift_label", "btn_extend_label",
    "btn_balance_label",
    "btn_buy_emoji", "btn_my_keys_emoji", "btn_status_emoji",
    "btn_payments_emoji", "btn_profile_emoji", "btn_support_emoji",
    "btn_trial_emoji", "btn_gift_emoji", "btn_extend_emoji",
    "btn_balance_emoji",
    "btn_buy_style", "btn_my_keys_style", "btn_status_style",
    "btn_payments_style", "btn_profile_style", "btn_support_style",
    "btn_trial_style", "btn_gift_style", "btn_extend_style",
    "btn_balance_style",
    "ps_sbp_enabled",
    "trial_enabled", "trial_days", "trial_label",
    "maintenance_mode", "maintenance_message",
    "notify_monitoring_enabled", "notify_svc_database", "notify_svc_telegram_bot",
    "notify_svc_vpn_panel", "notify_svc_yookassa", "notify_svc_cryptobot",
    "notify_svc_freekassa", "notify_cooldown_seconds", "notify_on_degraded",
    "notify_expiry_enabled", "notify_expiry_days", "notify_expiry_message",
    "notify_chat_ids",
    "bot_enabled", "bot_language",
    "referral_bonus_type", "referral_bonus_value",
    "traffic_abuse_threshold_gb", "traffic_abuse_speed_limit_mbps",
    "required_channel_id", "required_channel_name",
    "logo_url",
    "photo_welcome", "photo_buy", "photo_my_keys", "photo_balance",
    "photo_about", "photo_support", "photo_profile", "photo_language", "photo_trial",
})


def _mask(value: str) -> str:
    if not value or len(value) <= 4:
        return "****"
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


class PaymentSystemConfig(BaseModel):
    enabled: Optional[bool] = None
    shop_id: Optional[str] = None
    api_key: Optional[str] = None
    secret: Optional[str] = None
    secret_word_1: Optional[str] = None
    secret_word_2: Optional[str] = None
    token: Optional[str] = None
    merchant_id: Optional[str] = None
    rate: Optional[str] = None


@router.get("/")
async def get_settings(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    svc = BotSettingsService(db)
    settings = await svc.get_all()
    return {k: _mask(v) if k in _SENSITIVE_KEYS else v for k, v in settings.items()}


@router.patch("/")
async def update_settings(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    invalid_keys = [k for k in body if k not in _ALLOWED_SETTINGS_KEYS]
    if invalid_keys:
        raise HTTPException(status_code=400, detail=f"Unknown settings keys: {', '.join(invalid_keys[:10])}")
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


@router.get("/payment-systems/detail")
async def get_payment_systems_detail(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    svc = BotSettingsService(db)
    settings = await svc.get_all()
    systems = {}
    ps_keys = {k: v for k, v in settings.items() if k.startswith("ps_")}
    for key, val in ps_keys.items():
        name = key.replace("ps_", "").replace("_enabled", "")
        if name not in systems:
            systems[name] = {"enabled": False, "config": {}}
        if key.endswith("_enabled"):
            systems[name]["enabled"] = val == "1"
        else:
            config_key = key.replace(f"ps_{name}_", "")
            systems[name]["config"][config_key] = val

    # Add additional config keys per payment system (mask sensitive values)
    for name in systems:
        if name == "yookassa":
            raw = settings.get("yookassa_secret_key_override", "")
            systems[name]["config"]["shop_id"] = settings.get("yookassa_shop_id", "")
            systems[name]["config"]["secret_key"] = _mask(raw) if raw else ""
        elif name == "cryptobot":
            raw = settings.get("cryptobot_token", "")
            systems[name]["config"]["token"] = _mask(raw) if raw else ""
            systems[name]["config"]["rate"] = settings.get("stars_rate", "1.5")
        elif name == "freekassa":
            systems[name]["config"]["shop_id"] = settings.get("freekassa_shop_id", "")
            systems[name]["config"]["api_key"] = _mask(settings.get("freekassa_api_key", ""))
            systems[name]["config"]["secret_word_1"] = _mask(settings.get("freekassa_secret_word_1", ""))
            systems[name]["config"]["secret_word_2"] = _mask(settings.get("freekassa_secret_word_2", ""))
        elif name == "aikassa":
            raw = settings.get("aikassa_token", "")
            systems[name]["config"]["shop_id"] = settings.get("aikassa_shop_id", "")
            systems[name]["config"]["token"] = _mask(raw) if raw else ""
        elif name == "platega":
            raw = settings.get("platega_secret", "")
            systems[name]["config"]["merchant_id"] = settings.get("platega_merchant_id", "")
            systems[name]["config"]["secret"] = _mask(raw) if raw else ""
        elif name == "paypalych":
            raw = settings.get("paypalych_api_token", "")
            systems[name]["config"]["api_token"] = _mask(raw) if raw else ""

    return systems


@router.post("/payment-systems/{name}/configure")
async def configure_payment_system(
    name: str,
    body: PaymentSystemConfig,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    svc = BotSettingsService(db)
    updates = {}

    # Enable/disable
    if body.enabled is not None:
        updates[f"ps_{name}_enabled"] = "1" if body.enabled else "0"

    # System-specific config
    if name == "yookassa":
        if body.shop_id is not None:
            updates["yookassa_shop_id"] = body.shop_id
        if body.secret is not None:
            updates["yookassa_secret_key_override"] = body.secret
    elif name == "cryptobot":
        if body.token is not None:
            updates["cryptobot_token"] = body.token
        if body.rate is not None:
            updates["stars_rate"] = body.rate
    elif name == "freekassa":
        if body.shop_id is not None:
            updates["freekassa_shop_id"] = body.shop_id
        if body.api_key is not None:
            updates["freekassa_api_key"] = body.api_key
        if body.secret_word_1 is not None:
            updates["freekassa_secret_word_1"] = body.secret_word_1
        if body.secret_word_2 is not None:
            updates["freekassa_secret_word_2"] = body.secret_word_2
    elif name == "aikassa":
        if body.shop_id is not None:
            updates["aikassa_shop_id"] = body.shop_id
        if body.token is not None:
            updates["aikassa_token"] = body.token
    elif name == "platega":
        if body.merchant_id is not None:
            updates["platega_merchant_id"] = body.merchant_id
        if body.secret is not None:
            updates["platega_secret"] = body.secret
    elif name == "paypalych":
        if body.token is not None:
            updates["paypalych_api_token"] = body.token
    elif name == "stars":
        if body.rate is not None:
            updates["stars_rate"] = body.rate

    if updates:
        await svc.set_many(updates)
        await db.commit()

    return {"ok": True, **updates}


@router.post("/payment-systems/{name}/test")
async def test_payment_system(
    name: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    svc = BotSettingsService(db)
    settings = await svc.get_all()

    if name == "yookassa":
        shop_id = settings.get("yookassa_shop_id", "")
        secret = settings.get("yookassa_secret_key_override", "")
        if not shop_id or not secret:
            return {"ok": False, "detail": "YooKassa не настроен: отсутствуют shop_id или secret_key"}
        try:
            from yookassa import Configuration
            Configuration.account_id = shop_id
            Configuration.secret_key = secret
            from yookassa import Me
            me = Me.info()
            return {"ok": True, "detail": f"YooKassa: {me.account_id}"}
        except Exception as e:
            return {"ok": False, "detail": f"YooKassa: {e}"}
    elif name == "cryptobot":
        token = settings.get("cryptobot_token", "")
        if not token:
            return {"ok": False, "detail": "CryptoBot не настроен: отсутствует токен"}
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.cryptobot.ai/api/v1/me",
                    headers={"Crypto-Pay-API-Token": token},
                )
                if resp.status_code == 200:
                    return {"ok": True, "detail": "CryptoBot: подключение успешно"}
                return {"ok": False, "detail": f"CryptoBot: HTTP {resp.status_code}"}
        except Exception as e:
            return {"ok": False, "detail": f"CryptoBot: {e}"}
    else:
        return {"ok": True, "detail": f"{name}: проверка не реализована, сохранено"}


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
