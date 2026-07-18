"""Утилита для получения главного меню с настройками из БД."""

import json
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from aiogram.types import InlineKeyboardMarkup
from app.bot.keyboards.main import main_menu_kb, _DEFAULT_LAYOUT
from app.services.bot_settings import BotSettingsService
from app.core.config import config

_BUTTON_IDS = [
    "my_keys",
    "buy",
    "profile",
    "balance",
    "promo",
    "support",
    "connect",
    "about",
    "servers",
    "top_referrers",
    "status",
    "language",
    "trial",
    "cabinet",
    "admin_menu",
    "admin_panel",
]

# Default labels buttons
_BTN_LABELS: dict[str, dict[str, str]] = {
    "ru": {
        "my_keys": "🔑 Мои подписки",
        "buy": "💳 Купить",
        "profile": "👤 Профиль",
        "balance": "💰 Баланс",
        "promo": "🎁 Промокод",
        "support": "💬 Поддержка",
        "connect": "📲 Как подключить",
        "about": "ℹ️ О проекте",
        "servers": "🌐 Серверы",
        "top_referrers": "🏆 Топ рефереров",
        "status": "📊 Статус",
        "language": "🌐 Язык",
        "trial": "🎁 Пробный период",
        "cabinet": "📱 Кабинет",
        "admin_panel": "⚙️ Админ панель",
        "admin_menu": "ℹ️ Админ меню"
    },
    "en": {
        "my_keys": "🔑 My subscriptions",
        "buy": "💳 Buy",
        "profile": "👤 Profile",
        "balance": "💰 Balance",
        "promo": "🎁 Promo code",
        "support": "💬 Support",
        "connect": "📲 How to connect",
        "about": "ℹ️ About",
        "servers": "🌐 Servers",
        "top_referrers": "🏆 Top referrers",
        "status": "📊 Status",
        "language": "🌐 Language",
        "trial": "🎁 Trial period",
        "cabinet": "📱 Cabinet",
        "admin_panel": "⚙️ Admin panel",
        "admin_menu": "ℹ️ Admin menu"
    },
    "fa": {
        "my_keys": "🔑 اشتراک‌های من",
        "buy": "💳 خرید",
        "profile": "👤 پروفایل",
        "balance": "💰 موجودی",
        "promo": "🎁 کد تخفیف",
        "support": "💬 پشتیبانی",
        "connect": "📲 نحوه اتصال",
        "about": "ℹ️ درباره",
        "servers": "🌐 سرورها",
        "top_referrers": "🏆 برترین معرفان",
        "status": "📊 وضعیت",
        "language": "🌐 زبان",
        "trial": "🎁 دوره آزمایشی",
        "cabinet": "📱 کابینت",
        "admin_panel": "⚙️ پنل مدیریت",
        "admin_menu": "ℹ️ منوی مدیریت"
    },
}


def _resolve_url(settings: dict, key: str, fallback_path: str) -> str:
    """Resolve a URL from settings, falling back to site_url + path."""
    url = settings.get(key, "").strip()
    if url:
        return url
    site = config.web.site_url
    if site:
        return site.rstrip("/") + fallback_path
    return ""


def _append_query_param(url: str, key: str, value: str) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query[key] = value
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
    )


def _translate_layout(layout: list, lang: str, settings: dict) -> list:
    """Translate button labels in layout based on user language, with admin overrides."""
    result = []
    for row in layout:
        if not row or not isinstance(row, list):
            continue
        new_row = []
        for b in row:
            if not isinstance(b, dict) or not b.get("label"):
                continue
            bid = b.get("id", "")
            override = settings.get(f"i18n_{lang}_btn_{bid}", "").strip()
            if not override:
                override = settings.get(f"btn_{bid}", "").strip()
            default_label = _BTN_LABELS.get(lang, _BTN_LABELS["ru"]).get(
                bid, b.get("label", "")
            )
            label = override if override else default_label
            new_row.append({**b, "label": label})
        if new_row:
            result.append(new_row)
    return result


def _resolve_layout_urls(layout: list, settings: dict, is_admin: bool) -> list:
    """Resolve cabinet and admin_panel URLs, remove if no URL, hide admin-only buttons."""
    result = []
    for row in layout:
        if not row or not isinstance(row, list):
            continue
        new_row = []
        for b in row:
            if not isinstance(b, dict):
                continue
            bid = b.get("id", "")
            if bid == "cabinet":
                url = _resolve_url(settings, "cabinet_url", "/cabinet/")
                if not url:
                    continue
                url = _append_query_param(url, "miniapp", "1")
                new_row.append({**b, "web_app": url, "url": "", "callback": ""})
            elif bid == "admin_panel":
                if not is_admin:
                    continue
                url = _resolve_url(settings, "admin_panel_url", config.web.panel_root)
                if not url:
                    continue
                new_row.append({**b, "url": url, "web_app": "", "callback": ""})
            else:
                new_row.append(b)
        if new_row:
            result.append(new_row)
    return result


def _resolve_layout_menu(layout: list, is_admin: bool) -> list:
    """Normalize admin menu button callback and hide it for non-admins."""
    result = []
    for row in layout:
        if not row or not isinstance(row, list):
            continue
        new_row = []
        for b in row:
            if not isinstance(b, dict):
                continue
            bid = b.get("id", "")
            if bid == "admin_menu":
                if not is_admin:
                    continue
                new_row.append(
                    {**b, "callback": "admin:panel", "url": "", "web_app": ""}
                )
            else:
                new_row.append(b)
        if new_row:
            result.append(new_row)
    return result


async def get_main_menu_kb(
    session, lang: str = "ru", user_id: int = None, is_admin: bool = False
) -> InlineKeyboardMarkup:
    s = await BotSettingsService(session).get_all()

    # Load layout (support keyboard_layout JSON, btn_order JSON, and btn_order CSV)
    raw_layout = s.get("keyboard_layout", "")
    raw_btn_order = s.get("btn_order", "")
    try:
        layout = json.loads(raw_layout) if raw_layout else None
    except Exception:
        layout = None

    if not layout and raw_btn_order:
        try:
            parsed_order = json.loads(raw_btn_order)
            if isinstance(parsed_order, list) and all(isinstance(r, list) for r in parsed_order):
                default_map = {}
                for row in _DEFAULT_LAYOUT:
                    for b in row:
                        default_map[b["id"]] = b
                layout = []
                for row in parsed_order:
                    full_row = []
                    for bid in row:
                        if bid in default_map:
                            full_row.append(default_map[bid])
                    if full_row:
                        layout.append(full_row)
        except Exception:
            pass

    if not layout and raw_btn_order:
        order_ids = [x.strip() for x in raw_btn_order.split(",") if x.strip()]
        if order_ids:
            default_map = {}
            for row in _DEFAULT_LAYOUT:
                for b in row:
                    default_map[b["id"]] = b
            layout = []
            for bid in order_ids:
                if bid in default_map:
                    layout.append([default_map[bid]])
            if not layout:
                layout = None

    if not layout:
        layout = _DEFAULT_LAYOUT

    if user_id and s.get("trial_enabled", "0") == "1":
        from sqlalchemy import select
        from app.models.vpn_key import VpnKey

        result = await session.execute(
            select(VpnKey).where(VpnKey.user_id == user_id).limit(1)
        )
        has_keys = result.scalar_one_or_none() is not None
        if has_keys:
            layout = [[b for b in row if b.get("id") != "trial"] for row in layout]
            layout = [row for row in layout if row]

    # Resolve cabinet and admin_panel URLs from settings
    layout = _resolve_layout_urls(layout, s, is_admin)
    layout = _resolve_layout_menu(layout, is_admin)
    # Translate labels
    layout = _translate_layout(layout, lang, s)

    # Load styles (support both btn_style_{bid} and btn_{bid}_style)
    styles = {}
    for bid in _BUTTON_IDS:
        style = s.get(f"btn_style_{bid}", "").strip()
        if not style:
            style = s.get(f"btn_{bid}_style", "").strip()
        styles[bid] = style

    # Load custom emojis (support both btn_emoji_{bid} and btn_icon_{bid})
    emojis = {}
    for bid in _BUTTON_IDS:
        emoji = s.get(f"btn_emoji_{bid}", "").strip()
        if not emoji:
            emoji = s.get(f"btn_icon_{bid}", "").strip()
        emojis[bid] = emoji

    return main_menu_kb(
        support_url=s.get("support_url", ""),
        layout=layout,
        styles=styles,
        emojis=emojis,
        is_admin=is_admin,
    )
