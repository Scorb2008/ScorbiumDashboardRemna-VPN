from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_admin
from app.schemas.user import UserDetail, UserRead, UserUpdate
from app.schemas.payment import PaymentRead
from app.schemas.vpn import VpnKeyRead
from app.services.user import UserService
from app.services.payment import PaymentService
from app.services.vpn_key import VpnKeyService
from app.services.telegram_notify import TelegramNotifyService
from pydantic import BaseModel

router = APIRouter()


class SendMessageBody(BaseModel):
    text: str
    parse_mode: str = "HTML"


class BulkActionBody(BaseModel):
    user_ids: list[int]
    action: str  # ban, unban, set_balance
    value: str = ""


class GiveKeyBody(BaseModel):
    plan_id: int = 0
    days: int = 30


@router.post("/bulk", summary="Bulk action on users")
async def bulk_action(
    body: BulkActionBody,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
) -> dict:
    svc = UserService(db)
    results = {"success": 0, "errors": 0}
    for uid in body.user_ids:
        try:
            if body.action == "ban":
                await svc.ban(uid)
            elif body.action == "unban":
                await svc.unban(uid)
            elif body.action == "set_balance":
                await svc.update(uid, UserUpdate(balance=float(body.value)))
            elif body.action == "add_balance":
                await svc.add_balance(uid, float(body.value))
            else:
                continue
            results["success"] += 1
        except Exception:
            results["errors"] += 1
    await db.commit()
    return results


@router.post("/{user_id}/give-key", summary="Issue VPN key to user")
async def give_key(
    user_id: int,
    body: GiveKeyBody,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
) -> dict:
    user = await UserService(db).get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    plan_id = body.plan_id if body.plan_id else None
    if plan_id:
        from app.services.plan import PlanService
        plan = await PlanService(db).get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        key = await VpnKeyService(db).provision(user_id, plan)
    else:
        from datetime import datetime, timedelta, timezone
        from app.models.vpn_key import VpnKey, VpnKeyStatus
        key = VpnKey(
            user_id=user_id,
            status=VpnKeyStatus.ACTIVE.value,
            expires_at=datetime.now(timezone.utc) + timedelta(days=body.days),
        )
        db.add(key)
        await db.flush()

    if not key:
        raise HTTPException(status_code=500, detail="Failed to provision VPN key")

    await db.commit()
    return {"ok": True, "key_id": key.id, "user_id": user_id}


@router.get("/", summary="List users")
async def list_users(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    svc = UserService(db)
    items = await svc.get_all(limit=limit, offset=offset)
    total = await svc.count_all()
    return {"items": [UserRead.model_validate(u).model_dump() for u in items], "total": total, "limit": limit, "offset": offset}


@router.get("/{user_id}/keys", response_model=list[VpnKeyRead], summary="User VPN keys")
async def user_keys(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
) -> list[VpnKeyRead]:
    return await VpnKeyService(db).get_all_for_user(user_id)


@router.get(
    "/{user_id}/payments", response_model=list[PaymentRead], summary="User payments"
)
async def user_payments(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
) -> list[PaymentRead]:
    return await PaymentService(db).get_all(user_id=user_id)


@router.post("/{user_id}/message", summary="Send Telegram message to user")
async def send_message(
    user_id: int,
    body: SendMessageBody,
    _: str = Depends(get_current_admin),
) -> dict:
    notify = TelegramNotifyService()
    ok = await notify.send_message(user_id, body.text, body.parse_mode)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to send Telegram message",
        )
    return {"detail": "Message sent"}


@router.get("/{user_id}", response_model=UserDetail, summary="Get user details")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
) -> UserDetail:
    user = await UserService(db).get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    
    vpn_keys_count = await VpnKeyService(db).count_for_user(user_id)
    payments_count = await PaymentService(db).count_for_user(user_id)

    return UserDetail(
        **UserRead.model_validate(user).model_dump(),
        subscriptions_count=vpn_keys_count,
        payments_count=payments_count,
        vpn_keys_count=vpn_keys_count,
    )


@router.patch("/{user_id}", response_model=UserRead, summary="Update user")
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
) -> UserRead:
    user = await UserService(db).update(user_id, data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.post("/{user_id}/ban", response_model=UserRead, summary="Ban user")
async def ban_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
) -> UserRead:
    user = await UserService(db).ban(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.post("/{user_id}/unban", response_model=UserRead, summary="Unban user")
async def unban_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
) -> UserRead:
    user = await UserService(db).unban(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user
