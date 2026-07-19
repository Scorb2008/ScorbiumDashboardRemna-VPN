from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db, require_role
from app.services.audit import AuditService
from app.services.admin import AdminService

router = APIRouter()


@router.get("/")
async def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    action: str | None = None,
    admin_id: int | None = None,
    _admin=Depends(require_role("superadmin")),
    db: AsyncSession = Depends(get_db),
):
    svc = AuditService(db)
    entries, total = await svc.get_paginated(limit=limit, offset=offset, action=action, admin_id=admin_id)

    admin_ids = list({e.admin_id for e in entries})
    admins_map: dict[int, dict] = {}
    if admin_ids:
        admins = await AdminService(db).get_by_ids(admin_ids)
        admins_map = {a.id: {"username": a.username, "role": a.role} for a in admins}

    items = []
    for e in entries:
        admin_info = admins_map.get(e.admin_id, {"username": f"admin#{e.admin_id}", "role": "unknown"})
        items.append({
            "id": e.id,
            "admin_id": e.admin_id,
            "admin_username": admin_info["username"],
            "admin_role": admin_info["role"],
            "action": e.action,
            "target_type": e.target_type,
            "target_id": e.target_id,
            "details": e.details,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        })
    return {"items": items, "total": total, "limit": limit, "offset": offset}
