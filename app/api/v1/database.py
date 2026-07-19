"""REST API endpoints for database management."""

import csv
import gzip
import io
import logging
import subprocess

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_admin, require_role
from app.core.config import config
from app.models.payment import Payment
from app.models.support import SupportTicket
from app.models.user import User
from app.models.vpn_key import VpnKey

router = APIRouter()


class ClearConfirmBody(BaseModel):
    confirm: str


@router.get("/stats")
async def db_stats(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    vpn_keys = (await db.execute(select(func.count()).select_from(VpnKey))).scalar_one()
    payments = (await db.execute(select(func.count()).select_from(Payment))).scalar_one()
    tickets = (await db.execute(select(func.count()).select_from(SupportTicket))).scalar_one()
    return {
        "users": users or 0,
        "vpn_keys": vpn_keys or 0,
        "payments": payments or 0,
        "tickets": tickets or 0,
    }


@router.get("/export")
async def db_export(
    _admin=Depends(require_role("superadmin")),
    format: str = "sql",
):
    pg_uri = config.database.sync_dsn
    cmd = [
        "pg_dump",
        "--no-password",
        "--clean",
        "--if-exists",
        "--no-owner",
        "--no-privileges",
        pg_uri,
    ]
    try:
        import asyncio
        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, timeout=120
        )
        if result.returncode != 0:
            logging.getLogger(__name__).error("pg_dump failed: %s", result.stderr.decode(errors="replace")[:500])
            raise HTTPException(status_code=500, detail="Database export failed")
        sql_bytes = result.stdout
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="pg_dump not found")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="pg_dump timed out")

    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    if format == "gz":
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
            gz.write(sql_bytes)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/gzip",
            headers={"Content-Disposition": f'attachment; filename="backup_{ts}.sql.gz"'},
        )

    return StreamingResponse(
        io.BytesIO(sql_bytes),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="backup_{ts}.sql"'},
    )


@router.post("/clear")
async def db_clear(
    body: ClearConfirmBody,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_role("superadmin")),
):
    if body.confirm != "DELETE EVERYTHING":
        raise HTTPException(status_code=400, detail='Send {"confirm": "DELETE EVERYTHING"} to proceed')
    try:
        await db.execute(text("DELETE FROM ticket_messages"))
        await db.execute(text("DELETE FROM referrals"))
        await db.execute(text("DELETE FROM support_tickets"))
        await db.execute(text("DELETE FROM payments"))
        await db.execute(text("DELETE FROM vpn_keys"))
        await db.execute(text("DELETE FROM users"))
        await db.commit()
        return {"ok": True, "message": "Database cleared successfully"}
    except Exception as e:
        await db.rollback()
        logging.getLogger(__name__).error("db_clear failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Database clear failed")


@router.get("/export/users")
async def export_users_csv(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_role("superadmin")),
):
    from datetime import datetime, timezone

    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    buf = io.BytesIO()
    buf.write(b'\xef\xbb\xbf')  # UTF-8 BOM for Excel
    text_buf = io.TextIOWrapper(buf, encoding='utf-8', write_through=True)
    writer = csv.writer(text_buf)
    writer.writerow(["id", "username", "full_name", "is_active", "is_banned", "balance", "language", "autorenew", "last_seen"])

    offset = 0
    page_size = 1000
    while True:
        result = await db.execute(select(User).order_by(User.id).offset(offset).limit(page_size))
        users = list(result.scalars().all())
        if not users:
            break
        for u in users:
            writer.writerow([
                u.id,
                u.username or "",
                u.full_name,
                u.is_active,
                u.is_banned,
                float(u.balance or 0),
                u.language or "",
                u.autorenew,
                u.last_seen.isoformat() if u.last_seen else "",
            ])
        offset += page_size

    text_buf.flush()
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="users_{ts}.csv"'},
    )


@router.get("/export/payments")
async def export_payments_csv(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_role("superadmin")),
):
    from datetime import datetime, timezone

    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    buf = io.BytesIO()
    buf.write(b'\xef\xbb\xbf')  # UTF-8 BOM for Excel
    text_buf = io.TextIOWrapper(buf, encoding='utf-8', write_through=True)
    writer = csv.writer(text_buf)
    writer.writerow(["id", "user_id", "provider", "payment_type", "amount", "currency", "status", "external_id", "created_at"])

    offset = 0
    page_size = 1000
    while True:
        result = await db.execute(select(Payment).order_by(Payment.id).offset(offset).limit(page_size))
        payments = list(result.scalars().all())
        if not payments:
            break
        for p in payments:
            writer.writerow([
                p.id,
                p.user_id,
                p.provider,
                p.payment_type,
                float(p.amount or 0),
                p.currency,
                p.status,
                p.external_id or "",
                p.created_at.isoformat() if p.created_at else "",
            ])
        offset += page_size

    text_buf.flush()
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="payments_{ts}.csv"'},
    )
