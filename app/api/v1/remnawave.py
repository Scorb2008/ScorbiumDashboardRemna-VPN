"""Remnawave API proxy for the SPA frontend.

All Remnawave calls are proxied through the backend to avoid CORS issues."""

from fastapi import APIRouter, Depends, HTTPException, Request
from app.api.dependencies import get_current_admin
from app.services.remnawave.remnawave_api import RemnawaveClient
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
