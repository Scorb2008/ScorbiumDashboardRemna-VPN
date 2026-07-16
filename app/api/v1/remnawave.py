"""Remnawave API connectivity for the SPA frontend.

Returns connection info so the frontend can call Remnawave API directly."""

from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import get_current_admin
from app.services.remnawave.remnawave_api import RemnawaveClient
from app.core.config import config


router = APIRouter()


@router.get("/connect")
async def remnawave_connect(_admin=Depends(get_current_admin)):
    """Return Remnawave base URL + auth token for direct API calls from frontend."""
    try:
        client = RemnawaveClient()
        token = await client._get_token()
        base = str(config.remnawave.remnawave_admin_panel).rstrip("/")
        return {"base_url": base, "token": token}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Remnawave auth failed: {str(e)}")


@router.get("/status")
async def remnawave_status(_admin=Depends(get_current_admin)):
    """Quick health check — proxies a single request to /api/system/stats."""
    try:
        client = RemnawaveClient()
        from httpx import AsyncClient
        headers = await client._headers()
        base = str(config.remnawave.remnawave_admin_panel).rstrip("/")
        async with AsyncClient(timeout=15) as session:
            resp = await session.get(f"{base}/api/system/stats", headers=headers)
            if resp.status_code == 200:
                return {"connected": True, "stats": resp.json()}
            return {"connected": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"connected": False, "error": str(e)}
