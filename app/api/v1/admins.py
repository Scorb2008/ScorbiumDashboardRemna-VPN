"""REST API endpoints for admin management."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_admin
from app.services.admin import AdminService

router = APIRouter()


@router.get("/")
async def list_admins(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    admins = await AdminService(db).get_all()
    return [
        {
            "id": a.id,
            "username": a.username,
            "role": a.role,
            "is_active": a.is_active,
            "has_2fa": bool(a.totp_secret),
        }
        for a in admins
    ]


@router.get("/me")
async def current_admin(
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    svc = AdminService(db)
    a = await svc.get_by_username(admin["sub"])
    if not a:
        raise HTTPException(status_code=404, detail="Admin not found")
    return {
        "id": a.id,
        "username": a.username,
        "role": a.role,
        "is_active": a.is_active,
        "has_2fa": bool(a.totp_secret),
    }


@router.post("/")
async def create_admin(
    body: dict,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    if admin.get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="Only superadmin can create admins")
    username = body.get("username", "").strip()
    password = body.get("password", "").strip()
    role = body.get("role", "operator")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    if role not in ("superadmin", "manager", "operator"):
        raise HTTPException(status_code=400, detail="Invalid role")
    if role == "superadmin":
        raise HTTPException(status_code=403, detail="Cannot create superadmin via API")
    svc = AdminService(db)
    existing = await svc.get_by_username(username)
    if existing:
        raise HTTPException(status_code=409, detail="Admin already exists")
    a = await svc.create(username=username, password=password, role=role)
    await db.commit()
    return {
        "id": a.id,
        "username": a.username,
        "role": a.role,
        "is_active": a.is_active,
    }


@router.patch("/{admin_id}")
async def update_admin(
    admin_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    if admin.get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="Only superadmin can update admins")
    svc = AdminService(db)
    target = await svc.get_by_id(admin_id)
    if not target:
        raise HTTPException(status_code=404, detail="Admin not found")
    if admin["sub"] == target.username:
        new_role = body.get("role")
        if new_role and new_role != "superadmin":
            raise HTTPException(status_code=400, detail="Cannot demote yourself")
    updates = {}
    if "username" in body:
        updates["username"] = body["username"]
    if "password" in body and body["password"]:
        updates["password"] = body["password"]
    if "role" in body:
        if body["role"] == "superadmin":
            raise HTTPException(status_code=403, detail="Cannot promote to superadmin via API")
        updates["role"] = body["role"]
    if "is_active" in body:
        updates["is_active"] = body["is_active"]
    updated = await svc.update(admin_id, **updates)
    if "password" in body and body.get("password"):
        from app.services.token_blacklist import TokenBlacklistService
        await TokenBlacklistService(db).blacklist_all_for_user(target.username)
    await db.commit()
    return {"ok": True, "username": updated.username if updated else None}


@router.delete("/{admin_id}")
async def delete_admin(
    admin_id: int,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    if admin.get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="Only superadmin can delete admins")
    svc = AdminService(db)
    target = await svc.get_by_id(admin_id)
    if not target:
        raise HTTPException(status_code=404, detail="Admin not found")
    if admin["sub"] == target.username:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    await svc.delete(admin_id)
    await db.commit()
    return {"ok": True}
