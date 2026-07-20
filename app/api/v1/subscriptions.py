from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin, get_db
from app.schemas.vpn import VpnKeyRead
from app.services.vpn_key import VpnKeyService

router = APIRouter()


@router.get(
    "/", summary="List all VPN keys (subscriptions)"
)
async def list_subscriptions(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    svc = VpnKeyService(db)
    items = await svc.get_all(limit=limit, offset=offset)
    total = await svc.count()
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/{key_id}", response_model=VpnKeyRead, summary="Get VPN key")
async def get_subscription(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
) -> VpnKeyRead:
    key = await VpnKeyService(db).get_by_id(key_id)
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return key


@router.post("/{key_id}/cancel", response_model=VpnKeyRead, summary="Revoke VPN key")
async def cancel_subscription(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
) -> VpnKeyRead:
    key = await VpnKeyService(db).revoke(key_id)
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    await db.commit()
    return key


@router.post("/{key_id}/activate", response_model=VpnKeyRead, summary="Activate VPN key")
async def activate_subscription(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
) -> VpnKeyRead:
    key = await VpnKeyService(db).activate(key_id)
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    await db.commit()
    return key


@router.post("/{key_id}/deactivate", response_model=VpnKeyRead, summary="Deactivate VPN key")
async def deactivate_subscription(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
) -> VpnKeyRead:
    key = await VpnKeyService(db).deactivate(key_id)
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    await db.commit()
    return key


@router.delete("/{key_id}", summary="Delete VPN key permanently")
async def delete_subscription(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
) -> dict:
    key = await VpnKeyService(db).delete_key(key_id)
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    await db.commit()
    return {"ok": True, "detail": f"Key {key_id} deleted"}


@router.post("/give", summary="Issue a VPN key to user")
async def give_subscription(
    user_id: int,
    plan_id: int = 0,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
) -> dict:
    from app.services.user import UserService
    user = await UserService(db).get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    from datetime import datetime, timedelta, timezone
    from app.models.vpn_key import VpnKey, VpnKeyStatus
    key = VpnKey(
        user_id=user_id,
        plan_id=plan_id if plan_id else None,
        status=VpnKeyStatus.ACTIVE.value,
        expires_at=datetime.now(timezone.utc) + timedelta(days=days),
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)
    return {"ok": True, "key_id": key.id, "user_id": user_id}


@router.post("/expire-outdated", summary="Expire all outdated VPN keys")
async def expire_outdated(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
) -> dict:
    count = await VpnKeyService(db).expire_outdated()
    await db.commit()
    return {"expired": count}
