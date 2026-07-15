"""Remnawave JSON API endpoints for the SPA frontend."""

from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_admin
from app.services.remnawave.remnawave_api import RemnawaveService

router = APIRouter()


@router.get("/status")
async def remnawave_status(_admin=Depends(get_current_admin)):
    try:
        svc = RemnawaveService()
        stats = await svc.get_system_stats()
        return {"connected": True, "stats": stats}
    except Exception as e:
        return {"connected": False, "error": str(e)}


@router.get("/nodes")
async def remnawave_nodes(_admin=Depends(get_current_admin)):
    try:
        svc = RemnawaveService()
        data = await svc.get_nodes()
        if isinstance(data, dict):
            return data.get("nodes", [])
        return data if isinstance(data, list) else []
    except Exception:
        return []


@router.get("/users")
async def remnawave_users(_admin=Depends(get_current_admin)):
    try:
        svc = RemnawaveService()
        data = await svc.get_users(limit=200)
        if isinstance(data, dict):
            return data.get("users", [])
        return data if isinstance(data, list) else []
    except Exception:
        return []
