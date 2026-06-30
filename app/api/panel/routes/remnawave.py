"""Remnawave panel routes."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.services.remnawave.remnawave_api import RemnawaveService
from app.services.bot_settings import BotSettingsService

from .shared import _require_permission, _base_ctx, templates

router = APIRouter()


def _render_remnawave_status(remnawave_ok: bool, remnawave_stats: dict | None) -> str:
    if remnawave_ok:
        stats_html = ""
        if remnawave_stats:
            items = [
                (
                    "bi-cpu",
                    "rgba(0,212,170,.12)",
                    "#00d4aa",
                    "CPU",
                    f"{round(remnawave_stats.get('cpu_usage', 0), 1)}%",
                ),
                (
                    "bi-memory",
                    "rgba(16,185,129,.12)",
                    "#10b981",
                    "RAM",
                    f"{round((remnawave_stats.get('mem_used', 0) / 1048576), 1)} MB",
                ),
                (
                    "bi-hdd",
                    "rgba(245,158,11,.12)",
                    "#f59e0b",
                    "Disk",
                    f"{round((remnawave_stats.get('disk_used', 0) / 1073741824), 1)} GB",
                ),
            ]
            cards = "".join(
                f"""
                <div class="col-6 col-md-4">
                  <div style="background:var(--surface);border-radius:10px;padding:.75rem;text-align:center">
                    <div style="font-size:.8rem;color:{color};margin-bottom:.3rem"><i class="bi {icon}"></i></div>
                    <div style="font-size:1rem;font-weight:800;color:var(--text)">{value}</div>
                    <div style="font-size:.65rem;color:var(--text-muted)">{label}</div>
                  </div>
                </div>
                """
                for icon, _bg, color, label, value in items
            )
            stats_html = f'<div class="row g-2">{cards}</div>'

        return (
            '<div class="d-flex align-items-center gap-2 mb-3" style="color:var(--success);font-size:.85rem">'
            '<i class="bi bi-check-circle-fill"></i><span>Подключено</span></div>'
            f"{stats_html}"
        )

    return (
        '<div class="d-flex align-items-center gap-2" style="color:var(--danger);font-size:.85rem">'
        '<i class="bi bi-x-circle-fill"></i><span>Нет подключения</span></div>'
    )


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def remnawave_page(request: Request, db: AsyncSession = Depends(get_db)):
    _require_permission(request, "system")
    ctx = await _base_ctx(request, db, "remnawave")
    settings = await BotSettingsService(db).get_all()
    ctx["bot_settings"] = settings
    try:
        svc = RemnawaveService()
        ctx["remnawave_stats"] = await svc.get_system_stats()
        ctx["remnawave_ok"] = True
    except Exception:
        ctx["remnawave_stats"] = None
        ctx["remnawave_ok"] = False
    return templates.TemplateResponse("remnawave.html", ctx)


@router.get("/status", response_class=HTMLResponse)
async def remnawave_status(request: Request):
    _require_permission(request, "system")
    try:
        svc = RemnawaveService()
        remnawave_stats = await svc.get_system_stats()
        remnawave_ok = True
    except Exception:
        remnawave_stats = None
        remnawave_ok = False
    return HTMLResponse(_render_remnawave_status(remnawave_ok, remnawave_stats))


@router.get("/users", response_class=HTMLResponse)
async def remnawave_users(request: Request):
    _require_permission(request, "system")
    import html

    try:
        svc = RemnawaveService()
        data = await svc.get_users(limit=50)
        users = data.get("users", []) if isinstance(data, dict) else data
    except Exception as e:
        return HTMLResponse(
            f'<div style="color:#ef4444">Ошибка: {html.escape(str(e))}</div>'
        )

    if not users:
        return HTMLResponse(
            '<div class="text-center py-4" style="color:#8892a4">Пользователей нет</div>'
        )

    from datetime import datetime as _dt

    def _fmt_date(d):
        if not d or d == "—":
            return "—"
        try:
            if isinstance(d, str):
                d = d.replace("Z", "+00:00")
                dt = _dt.fromisoformat(d)
            else:
                dt = _dt.fromtimestamp(d)
            return dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            return str(d)

    rows = ""
    for u in users:
        status = u.get("status", "")
        dot_class = {
            "active": "online",
            "expired": "offline",
            "disabled": "warning",
        }.get(status, "")
        status_label = {
            "active": "Активен",
            "expired": "Истёк",
            "disabled": "Отключён",
        }.get(status, status)
        traffic = u.get("userTraffic", {}) or {}
        used = round(traffic.get("usedTrafficBytes", 0) / 1073741824, 2)
        limit_bytes = u.get("dataLimit", 0) or 0
        limit_gb = round(limit_bytes / 1073741824, 1) if limit_bytes else 0
        limit_str = f"{limit_gb} GB" if limit_bytes else "∞"
        username = html.escape(str(u.get("shortUuid", "")))
        expire = _fmt_date(u.get("expireAt"))
        created = _fmt_date(u.get("createdAt"))
        traffic_color = (
            "#22c55e"
            if limit_gb == 0 or used < limit_gb * 0.8
            else ("#eab308" if used < limit_gb else "#ef4444")
        )
        rows += f"""<div class="user-row" style="gap:.5rem;padding:.5rem .75rem">
          <div style="flex:1;min-width:0">
            <div style="display:flex;align-items:center;gap:.5rem;flex-wrap:wrap">
              <span class="status-dot {dot_class}" style="flex-shrink:0"></span>
              <code style="color:var(--accent);font-size:.82rem">{username}</code>
              <span style="font-size:.7rem;color:{traffic_color};font-weight:600">{used} GB <span style="color:#8892a4;font-weight:400">/ {limit_str}</span></span>
            </div>
          </div>
          <div class="text-end" style="flex-shrink:0;min-width:130px">
            <div style="font-size:.72rem;color:var(--text-muted)">
              {status_label}
              <span style="color:#8892a4;margin-left:.4rem">до {expire}</span>
            </div>
            <div style="font-size:.65rem;color:#5a6478;margin-top:.1rem">с {created}</div>
          </div>
        </div>"""

    return HTMLResponse(f'<div class="p-1">{rows}</div>')


@router.get("/groups", response_class=HTMLResponse)
async def remnawave_groups(request: Request):
    _require_permission(request, "system")
    import html

    try:
        svc = RemnawaveService()
        groups = await svc.get_groups()
    except Exception as e:
        return HTMLResponse(
            f'<div style="color:#ef4444">Ошибка: {html.escape(str(e))}</div>'
        )

    if not groups:
        return HTMLResponse(
            '<div class="text-center py-4" style="color:#8892a4">Групп нет</div>'
        )

    rows = ""
    for g in groups:
        disabled = g.get("isDisabled", False)
        inbounds = ", ".join(g.get("inboundTags", []))
        group_name = html.escape(str(g.get("name", "")))
        rows += f"""<div class="group-row">
          <div style="flex:1;min-width:0">
            <code style="color:var(--accent);font-size:.85rem">{g.get("id")}</code>
            <span class="ms-2" style="font-size:.85rem;color:var(--text)">{group_name}</span>
            <div style="font-size:.7rem;color:#8892a4;margin-top:.15rem">{html.escape(inbounds)}</div>
          </div>
          <div class="text-end" style="flex-shrink:0">
            <span class="status-dot {"offline" if disabled else "online"}"></span>
            <span style="font-size:.75rem;color:var(--text-muted);margin-left:.3rem">{g.get("totalUsers", 0)} юз.</span>
          </div>
        </div>"""

    return HTMLResponse(f'<div class="p-2">{rows}</div>')


@router.get("/nodes", response_class=HTMLResponse)
async def remnawave_nodes(request: Request):
    _require_permission(request, "system")
    import html

    try:
        svc = RemnawaveService()
        data = await svc.get_nodes()
        nodes = data.get("nodes", []) if isinstance(data, dict) else data
    except Exception as e:
        return HTMLResponse(
            f'<div style="color:#ef4444">Ошибка: {html.escape(str(e))}</div>'
        )

    if not nodes:
        return HTMLResponse(
            '<div class="text-center py-4" style="color:#8892a4">Нод нет</div>'
        )

    rows = ""
    for n in nodes:
        is_connected = n.get("isConnected", False)
        dot_class = "online" if is_connected else "offline"
        status_label = "Подключена" if is_connected else "Ошибка"
        node_name = html.escape(str(n.get("name", "")))
        country = html.escape(str(n.get("countryCode", "")))
        node_addr = html.escape(str(n.get("address", "")))
        location_parts = [p for p in (country, node_addr) if p]
        location = " / ".join(location_parts) if location_parts else "—"
        rows += f"""<div class="node-row">
          <div style="flex:1;min-width:0">
            <code style="color:var(--accent);font-size:.85rem">{html.escape(str(n.get("id", "")))}</code>
            <span class="ms-2" style="font-size:.85rem;color:var(--text)">{node_name}</span>
            <div style="font-size:.7rem;color:#8892a4;margin-top:.15rem">{location}</div>
          </div>
          <div class="text-end" style="flex-shrink:0">
            <span class="status-dot {dot_class}"></span>
            <span style="font-size:.75rem;color:var(--text-muted);margin-left:.3rem">{status_label}</span>
          </div>
        </div>"""

    return HTMLResponse(f'<div class="p-2">{rows}</div>')
