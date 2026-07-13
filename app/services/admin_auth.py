import time
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import config
from app.models.admin import Admin, AdminRole
from app.services.admin import AdminService
from app.utils.log import log
from app.utils.security import hash_password

# ── Brute-force protection ─────────────────────────────────────────────────
# In-memory rate limiter: tracks failed attempts per username.
_FAILED_ATTEMPTS: dict[str, list[float]] = defaultdict(list)
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 300  # 5 minutes


def _is_locked_out(username: str) -> bool:
    now = time.time()
    attempts = _FAILED_ATTEMPTS[username]
    # Prune old entries
    _FAILED_ATTEMPTS[username] = [t for t in attempts if now - t < _LOCKOUT_SECONDS]
    return len(_FAILED_ATTEMPTS[username]) >= _MAX_ATTEMPTS


def _record_failure(username: str) -> None:
    _FAILED_ATTEMPTS[username].append(time.time())


def _clear_failures(username: str) -> None:
    _FAILED_ATTEMPTS.pop(username, None)


async def authenticate_admin_credentials(
    session: AsyncSession,
    username: str,
    password: str,
) -> Admin | None:
    """Authenticate admins against the DB, with env superadmin fallback."""
    if _is_locked_out(username):
        log.warning(
            "Admin login locked out for '{}' — too many failed attempts", username
        )
        return None

    service = AdminService(session)

    admin = await service.authenticate(username, password)
    if admin:
        _clear_failures(username)
        return admin

    expected_username = config.web.web_superadmin_username
    expected_password = config.web.web_superadmin_password.get_secret_value()
    if username != expected_username or password != expected_password:
        _record_failure(username)
        log.warning(
            "Failed admin login attempt for '{}' from memory store",
            username,
        )
        return None

    admin = await service.get_by_username(username)
    if admin:
        if not admin.is_active:
            _record_failure(username)
            return None
        if admin.role != AdminRole.SUPERADMIN.value:
            admin.role = AdminRole.SUPERADMIN.value
            await session.commit()
            await session.refresh(admin)
        _clear_failures(username)
        return admin

    admin = Admin(
        username=username,
        password_hash=hash_password(password),
        role=AdminRole.SUPERADMIN.value,
        is_active=True,
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    _clear_failures(username)
    return admin
