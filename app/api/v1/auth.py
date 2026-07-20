import hashlib
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.services.admin_auth import authenticate_admin_credentials
from app.utils.security import create_access_token, decode_access_token_full

router = APIRouter()

_TEMP_TOKEN_EXPIRE = timedelta(minutes=5)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TwoFAChallengeResponse(BaseModel):
    requires_2fa: bool = True
    temp_token: str
    token_type: str = "bearer"


class TwoFARequestBody(BaseModel):
    temp_token: str
    code: str


@router.post("/login", summary="Admin login")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    admin = await authenticate_admin_credentials(db, form.username, form.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if admin.totp_secret:
        temp_token = create_access_token(
            subject=admin.username,
            role=admin.role,
            expires_delta=_TEMP_TOKEN_EXPIRE,
            extra={"type": "2fa_pending", "admin_id": admin.id},
        )
        return TwoFAChallengeResponse(temp_token=temp_token)

    token = create_access_token(
        subject=admin.username, role=admin.role, extra={"type": "admin"}
    )
    return TokenResponse(access_token=token)


@router.post("/2fa", response_model=TokenResponse, summary="Verify 2FA code")
async def verify_2fa_login(
    body: TwoFARequestBody,
    db: AsyncSession = Depends(get_db),
):
    info = decode_access_token_full(body.temp_token)
    if not info or info.get("type") != "2fa_pending":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired temp token",
        )

    import pyotp
    from app.services.admin import AdminService

    svc = AdminService(db)
    admin = await svc.get_by_username(info["sub"])
    if not admin or not admin.totp_secret:
        raise HTTPException(status_code=400, detail="2FA not configured for this account")

    totp = pyotp.TOTP(admin.totp_secret)
    if not totp.verify(body.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")

    token = create_access_token(
        subject=admin.username, role=admin.role, extra={"type": "admin"}
    )
    return TokenResponse(access_token=token)
