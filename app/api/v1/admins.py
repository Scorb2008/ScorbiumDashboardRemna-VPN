"""REST API endpoints for admin management."""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_admin, require_role
from app.services.admin import AdminService

router = APIRouter()


class AdminCreateBody(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8, max_length=128)
    role: Literal["manager", "operator"] = "operator"


class AdminUpdateBody(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=64)
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    role: Optional[Literal["manager", "operator"]] = None
    is_active: Optional[bool] = None


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
    body: AdminCreateBody,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_role("superadmin")),
):
    svc = AdminService(db)
    existing = await svc.get_by_username(body.username.strip())
    if existing:
        raise HTTPException(status_code=409, detail="Admin already exists")
    a = await svc.create(username=body.username.strip(), password=body.password, role=body.role)
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
    body: AdminUpdateBody,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_role("superadmin")),
):
    svc = AdminService(db)
    target = await svc.get_by_id(admin_id)
    if not target:
        raise HTTPException(status_code=404, detail="Admin not found")
    if admin["sub"] == target.username and body.role and body.role != "superadmin":
        raise HTTPException(status_code=400, detail="Cannot demote yourself")
    updates = {}
    if body.username is not None:
        updates["username"] = body.username.strip()
    if body.password is not None:
        updates["password"] = body.password
    if body.role is not None:
        updates["role"] = body.role
    if body.is_active is not None:
        updates["is_active"] = body.is_active
    if not updates:
        return {"ok": True}
    updated = await svc.update(admin_id, **updates)
    if body.password:
        from app.services.token_blacklist import TokenBlacklistService
        await TokenBlacklistService(db).blacklist_all_for_user(target.username)
    await db.commit()
    return {"ok": True, "username": updated.username if updated else None}


@router.delete("/{admin_id}")
async def delete_admin(
    admin_id: int,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_role("superadmin")),
):
    svc = AdminService(db)
    target = await svc.get_by_id(admin_id)
    if not target:
        raise HTTPException(status_code=404, detail="Admin not found")
    if admin["sub"] == target.username:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    await svc.delete(admin_id)
    await db.commit()
    return {"ok": True}
