import time
from collections import defaultdict, deque

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import config
from app.utils.rate_limit import disable_redis_client, get_redis_client

# ── Config ────────────────────────────────────────────────────────────────────
PANEL_WINDOW = 60
PANEL_MAX_REQUESTS = 120
API_WINDOW = 60
API_MAX_REQUESTS = 60
LOGIN_WINDOW = 300
LOGIN_MAX_ATTEMPTS = 10
BLOCK_DURATION = 300

# Per-user cabinet rate limiting
CABINET_USER_WINDOW = 60
CABINET_USER_MAX_REQUESTS = 30


_WHITELIST_PREFIXES = ("/docs", "/redoc", "/openapi")
_WHITELIST_EXACT = {"/health", "/api/v1/health/", "/favicon.ico"}
_PANEL_LOGIN_PATHS = {
    config.web.panel_login_path,
    f"{config.web.panel_prefix}/api/login",
    "/api/v1/auth/login",
}


def _extract_user_id_from_cookie(request: Request) -> int | None:
    """Extract user_id from the cabinet session cookie."""
    cookie = request.cookies.get("cabinet_session") or request.headers.get("X-Cabinet-User")
    if not cookie:
        return None
    try:
        uid = int(cookie.split(":")[0])
        return uid if uid > 0 else None
    except (ValueError, IndexError):
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._panel_hits: dict[str, deque] = defaultdict(deque)
        self._api_hits: dict[str, deque] = defaultdict(deque)
        self._login_hits: dict[str, deque] = defaultdict(deque)
        self._cabinet_user_hits: dict[int, deque] = defaultdict(deque)
        self._cabinet_user_blocked: dict[int, float] = {}
        self._blocked: dict[str, float] = {}
        self._last_cleanup = time.monotonic()

    def _get_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _check(self, hits: deque, window: int, max_req: int, ip: str) -> bool:
        now = time.monotonic()
        cutoff = now - window
        while hits and hits[0] < cutoff:
            hits.popleft()
        hits.append(now)
        if len(hits) > max_req:
            self._blocked[ip] = now + BLOCK_DURATION
            return True
        return False

    def _check_cabinet_user(self, user_id: int) -> bool:
        now = time.monotonic()
        if user_id in self._cabinet_user_blocked:
            if now < self._cabinet_user_blocked[user_id]:
                return True
            del self._cabinet_user_blocked[user_id]
        hits = self._cabinet_user_hits[user_id]
        cutoff = now - CABINET_USER_WINDOW
        while hits and hits[0] < cutoff:
            hits.popleft()
        hits.append(now)
        if len(hits) > CABINET_USER_MAX_REQUESTS:
            self._cabinet_user_blocked[user_id] = now + BLOCK_DURATION
            return True
        return False

    def _cleanup(self) -> None:
        now = time.monotonic()
        if now - self._last_cleanup < 60:
            return
        self._last_cleanup = now

        for storage, window in (
            (self._panel_hits, PANEL_WINDOW),
            (self._api_hits, API_WINDOW),
            (self._login_hits, LOGIN_WINDOW),
        ):
            cutoff = now - window
            stale_keys = []
            for key, hits in storage.items():
                while hits and hits[0] < cutoff:
                    hits.popleft()
                if not hits:
                    stale_keys.append(key)
            for key in stale_keys:
                storage.pop(key, None)

        cabinet_cutoff = now - CABINET_USER_WINDOW
        stale_users = []
        for uid, hits in self._cabinet_user_hits.items():
            while hits and hits[0] < cabinet_cutoff:
                hits.popleft()
            if not hits:
                stale_users.append(uid)
        for uid in stale_users:
            self._cabinet_user_hits.pop(uid, None)

        expired_blocks = [
            ip for ip, blocked_until in self._blocked.items() if blocked_until <= now
        ]
        for ip in expired_blocks:
            self._blocked.pop(ip, None)

        expired_user_blocks = [
            uid for uid, until in self._cabinet_user_blocked.items() if until <= now
        ]
        for uid in expired_user_blocks:
            self._cabinet_user_blocked.pop(uid, None)

    def _is_rate_limited(self, ip: str, path: str, method: str) -> bool:
        now = time.monotonic()
        if ip in self._blocked:
            if now < self._blocked[ip]:
                return True
            del self._blocked[ip]

        if path in _PANEL_LOGIN_PATHS.union({"/cabinet/auth", "/cabinet/auth/"}) and method == "POST":
            return self._check(
                self._login_hits[ip], LOGIN_WINDOW, LOGIN_MAX_ATTEMPTS, ip
            )

        is_api = path.startswith("/api/")
        if is_api:
            return self._check(self._api_hits[ip], API_WINDOW, API_MAX_REQUESTS, ip)
        return self._check(self._panel_hits[ip], PANEL_WINDOW, PANEL_MAX_REQUESTS, ip)

    async def _is_rate_limited_redis(self, ip: str, path: str, method: str) -> bool:
        redis = await get_redis_client()
        if not redis:
            return self._is_rate_limited(ip, path, method)

        if path in _PANEL_LOGIN_PATHS.union({"/cabinet/auth", "/cabinet/auth/"}) and method == "POST":
            scope = "login"
            window = LOGIN_WINDOW
            max_requests = LOGIN_MAX_ATTEMPTS
        elif path.startswith("/api/"):
            scope = "api"
            window = API_WINDOW
            max_requests = API_MAX_REQUESTS
        else:
            scope = "panel"
            window = PANEL_WINDOW
            max_requests = PANEL_MAX_REQUESTS

        try:
            block_key = f"rate_limit:block:{ip}"
            if await redis.exists(block_key):
                return True

            hits_key = f"rate_limit:hits:{scope}:{ip}"
            count = await redis.incr(hits_key)
            if count == 1:
                await redis.expire(hits_key, window)

            if count > max_requests:
                await redis.set(block_key, "1", ex=BLOCK_DURATION)
                return True

            return False
        except Exception as exc:
            await disable_redis_client(str(exc))
            return self._is_rate_limited(ip, path, method)

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        self._cleanup()
        if (
            path in _WHITELIST_EXACT
            or any(path.startswith(p) for p in _WHITELIST_PREFIXES)
            or path.startswith("/static/")
        ):
            return await call_next(request)

        ip = self._get_ip(request)
        if await self._is_rate_limited_redis(ip, path, request.method):
            if path.startswith("/api/") or request.headers.get("accept", "").startswith(
                "application/json"
            ):
                return JSONResponse(
                    {"detail": "Too many requests. Try again later."},
                    status_code=429,
                    headers={"Retry-After": str(BLOCK_DURATION)},
                )
            return Response(
                content=(
                    "<html><body style='background:#080812;color:#ef4444;"
                    "font-family:sans-serif;text-align:center;padding:4rem'>"
                    "<h2>⏳ Too Many Requests</h2>"
                    "<p>Подождите немного и попробуйте снова.</p>"
                    "</body></html>"
                ),
                status_code=429,
                media_type="text/html",
                headers={"Retry-After": str(BLOCK_DURATION)},
            )

        # Per-user cabinet rate limiting (non-IP)
        if path.startswith("/cabinet/") and path != "/cabinet/auth" and request.method != "GET":
            user_id = _extract_user_id_from_cookie(request)
            if user_id and self._check_cabinet_user(user_id):
                if request.headers.get("accept", "").startswith("application/json"):
                    return JSONResponse(
                        {"detail": "Too many requests. Try again later."},
                        status_code=429,
                        headers={"Retry-After": str(CABINET_USER_WINDOW)},
                    )
                return Response(
                    content="Too many requests. Try again later.",
                    status_code=429,
                    media_type="text/plain",
                    headers={"Retry-After": str(CABINET_USER_WINDOW)},
                )

        return await call_next(request)
