"""REST API endpoints for admin management."""

import base64
import io
import secrets
from typing import Literal, Optional

import pyotp
import qrcode
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_admin, require_role
from app.services.admin import AdminService

router = APIRouter()


class AdminCreateBody(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8, max_length=128)
    role: Literal["superadmin", "manager", "operator"] = "operator"


class AdminUpdateBody(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=64)
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    role: Optional[Literal["superadmin", "manager", "operator"]] = None
    is_active: Optional[bool] = None


class TwoFAVerifyBody(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


class TwoFADisableBody(BaseModel):
    password: str = Field(...)


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


# ── 2FA ──────────────────────────────────────────────────────────────────────


def _generate_backup_codes(count: int = 8) -> list[str]:
    return [secrets.token_hex(4).upper() for _ in range(count)]


def _backup_codes_hash(codes: list[str]) -> str:
    import hashlib
    return "\n".join(hashlib.sha256(c.encode()).hexdigest()[:16] for c in codes)


def _verify_backup_code(plain: str, stored_hash: str) -> bool:
    import hashlib
    h = hashlib.sha256(plain.encode()).hexdigest()[:16]
    for line in stored_hash.split("\n"):
        if line.strip() == h:
            return True
    return False


@router.post("/2fa/setup")
async def setup_2fa(
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    svc = AdminService(db)
    a = await svc.get_by_username(admin["sub"])
    if not a:
        raise HTTPException(status_code=404, detail="Admin not found")

    if a.totp_secret:
        raise HTTPException(status_code=400, detail="2FA already enabled. Disable it first.")

    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=a.username,
        issuer_name="Scorbium VPN",
    )

    qr = qrcode.make(provisioning_uri)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    backup_codes = _generate_backup_codes()
    a.totp_secret = secret
    a.backup_codes = _backup_codes_hash(backup_codes)
    await db.flush()

    return {
        "secret": secret,
        "otpauth_url": provisioning_uri,
        "qr_code": f"data:image/png;base64,{qr_b64}",
        "backup_codes": backup_codes,
    }


@router.post("/2fa/verify")
async def verify_2fa_enable(
    body: TwoFAVerifyBody,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    svc = AdminService(db)
    a = await svc.get_by_username(admin["sub"])
    if not a:
        raise HTTPException(status_code=404, detail="Admin not found")
    if not a.totp_secret:
        raise HTTPException(status_code=400, detail="Run /2fa/setup first")
    totp = pyotp.TOTP(a.totp_secret)
    if not totp.verify(body.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")
    return {"ok": True, "message": "2FA verified and enabled"}


@router.delete("/2fa")
async def disable_2fa(
    body: TwoFADisableBody,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    from app.utils.security import verify_password
    svc = AdminService(db)
    a = await svc.get_by_username(admin["sub"])
    if not a:
        raise HTTPException(status_code=404, detail="Admin not found")
    if not a.totp_secret:
        raise HTTPException(status_code=400, detail="2FA is not enabled")
    if not verify_password(body.password, a.password_hash):
        raise HTTPException(status_code=400, detail="Invalid password")
    a.totp_secret = None
    a.backup_codes = None
    await db.flush()
    return {"ok": True, "message": "2FA disabled"}


@router.post("/2fa/backup-verify")
async def verify_backup_code(
    body: TwoFAVerifyBody,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    svc = AdminService(db)
    a = await svc.get_by_username(admin["sub"])
    if not a:
        raise HTTPException(status_code=404, detail="Admin not found")
    if not a.backup_codes:
        raise HTTPException(status_code=400, detail="No backup codes available")
    if not _verify_backup_code(body.code.upper(), a.backup_codes):
        raise HTTPException(status_code=400, detail="Invalid backup code")
    return {"ok": True, "message": "Backup code accepted"}
