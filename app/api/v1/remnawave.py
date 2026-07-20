"""Remnawave API proxy for the SPA frontend.

All Remnawave calls are proxied through the backend to avoid CORS issues."""

from fastapi import APIRouter, Depends, HTTPException, Request
from app.api.dependencies import get_current_admin
from app.services.remnawave.remnawave_api import RemnawaveClient, RemnawaveService
from app.core.config import config


router = APIRouter()


@router.get("/connect")
async def remnawave_connect(_admin=Depends(get_current_admin)):
    """Return Remnawave base URL for display purposes."""
    base = str(config.remnawave.remnawave_admin_panel).rstrip("/")
    return {"base_url": base}


@router.get("/status")
async def remnawave_status(_admin=Depends(get_current_admin)):
    """Quick health check — proxies a single request to /api/system/stats."""
    try:
        client = RemnawaveClient()
        data = await client.get("/api/system/stats")
        return {"connected": True, "stats": data}
    except Exception as e:
        return {"connected": False, "error": str(e)}


@router.get("/nodes")
async def remnawave_nodes(_admin=Depends(get_current_admin)):
    """Return normalized list of Remnawave nodes with status."""
    svc = RemnawaveService()
    try:
        raw = await svc.get_nodes()
        nodes = raw.get("nodes", [])
        result = []
        for n in nodes:
            result.append({
                "uuid": n.get("uuid", ""),
                "name": n.get("name", ""),
                "address": n.get("address", n.get("ip", "")),
                "port": n.get("port"),
                "is_connected": n.get("isConnected", False),
                "is_active": n.get("isActive", True),
                "users_count": n.get("usersCount", n.get("userCount", 0)),
                "traffic_used": n.get("trafficUsedBytes", n.get("traffic_used", 0)),
                "traffic_limit": n.get("trafficLimitBytes", n.get("traffic_limit", 0)),
                "country_code": n.get("countryCode", ""),
                "location": n.get("countryCode", ""),
                "protocol": n.get("protocol", n.get("connection_type", "")),
                "created_at": n.get("createdAt", ""),
            })
        return {"nodes": result, "total": len(result)}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Remnawave error: {str(e)}")


@router.get("/stats")
async def remnawave_stats(_admin=Depends(get_current_admin)):
    """Return normalized system stats from Remnawave."""
    try:
        client = RemnawaveClient()
        data = await client.get("/api/system/stats")
        users = data.get("users", {})
        online = data.get("onlineStats", {})
        nodes = data.get("nodes", {})
        memory = data.get("memory", {})
        cpu = data.get("cpu", {})
        return {
            "connected": True,
            "online_users": online.get("onlineNow", 0),
            "total_users": users.get("totalUsers", 0),
            "active_users": users.get("activeUsers", users.get("totalUsers", 0)),
            "nodes_online": nodes.get("totalOnline", 0),
            "nodes_total": nodes.get("total", nodes.get("totalNodes", 0)),
            "cpu_usage": cpu.get("load", cpu.get("cores", 0)),
            "mem_used": memory.get("used", 0),
            "mem_total": memory.get("total", 0),
            "uptime": data.get("uptime", None),
            "raw": data,
        }
    except Exception as e:
        return {"connected": False, "error": str(e)}


@router.api_route(
    "/proxy/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    summary="Proxy arbitrary requests to Remnawave API",
)
async def remnawave_proxy(
    path: str,
    request: Request,
    _admin=Depends(get_current_admin),
):
    """Proxy any request to the Remnawave API panel.
    This avoids CORS issues by routing through the backend."""
    try:
        client = RemnawaveClient()
        method = request.method.lower()
        body = None
        if method in ("post", "put", "patch"):
            body = await request.json()
        params = dict(request.query_params) or None
        api_path = f"/{path}" if not path.startswith("/") else path
        result = await client._request(
            method.upper(),
            api_path,
            json=body,
            params=params,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Remnawave error: {str(e)}")
