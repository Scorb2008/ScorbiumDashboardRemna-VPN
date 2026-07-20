from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, desc, func
from app.models.audit_log import AuditLog


class AuditService:
    def __init__(self, session):
        self.session = session

    async def log(
        self,
        admin_id: int,
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        details: Optional[str] = None,
    ) -> AuditLog:
        entry = AuditLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def get_recent(self, limit: int | None = 20) -> list[AuditLog]:
        query = select(AuditLog).order_by(desc(AuditLog.created_at))
        if limit is not None:
            query = query.limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_paginated(
        self,
        limit: int = 50,
        offset: int = 0,
        action: Optional[str] = None,
        admin_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> tuple[list[AuditLog], int]:
        query = select(AuditLog)
        count_query = select(func.count()).select_from(AuditLog)
        filters = []
        if action is not None:
            filters.append(AuditLog.action == action)
        if admin_id is not None:
            filters.append(AuditLog.admin_id == admin_id)
        if date_from is not None:
            filters.append(AuditLog.created_at >= date_from)
        if date_to is not None:
            filters.append(AuditLog.created_at <= date_to)
        if filters:
            from sqlalchemy import and_
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        total = (await self.session.execute(count_query)).scalar_one()
        query = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_for_target(
        self, target_type: str, target_id: int, limit: int = 10
    ) -> list[AuditLog]:
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.target_type == target_type, AuditLog.target_id == target_id)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
