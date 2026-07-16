"""REST API endpoints for database management."""

import gzip
import io
import subprocess

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_admin
from app.core.config import config
from app.models.payment import Payment
from app.models.support import SupportTicket
from app.models.user import User
from app.models.vpn_key import VpnKey
from app.services.bot_settings import reset_bot_settings_cache

router = APIRouter()


@router.get("/stats")
async def db_stats(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    result = await db.execute(
        select(
            func.count().label("users"),
            select(func.count()).select_from(VpnKey).scalar_subquery().label("vpn_keys"),
            select(func.count()).select_from(Payment).scalar_subquery().label("payments"),
            select(func.count()).select_from(SupportTicket).scalar_subquery().label("tickets"),
        )
    )
    row = result.one()
    return {
        "users": row.users or 0,
        "vpn_keys": row.vpn_keys or 0,
        "payments": row.payments or 0,
        "tickets": row.tickets or 0,
        "admins": 0,
    }


@router.get("/export")
async def db_export(
    _admin=Depends(get_current_admin),
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
            raise HTTPException(status_code=500, detail=result.stderr.decode(errors="replace")[:300])
        sql_bytes = result.stdout
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="pg_dump not found")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="pg_dump timed out")

    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    from fastapi.responses import StreamingResponse

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
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
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
        raise HTTPException(status_code=500, detail=str(e))
