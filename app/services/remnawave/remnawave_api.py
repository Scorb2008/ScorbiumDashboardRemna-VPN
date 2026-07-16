import asyncio
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from httpx import AsyncClient, HTTPStatusError, RequestError

from app.core.config import config
from app.utils.log import log
from app.core.exceptions import RemnawaveRequestError, RemnawaveAuthError
from app.services.vpn_panel_interface import VpnPanelInterface


class RemnawaveClient:
    _token: Optional[str] = None
    _token_expires: Optional[datetime] = None
    _lock = asyncio.Lock()
    _session: Optional[AsyncClient] = None

    def __init__(self) -> None:
        cfg = config.remnawave
        if cfg is None:
            raise RuntimeError(
                "Remnawave is not configured. Check REMNAWAVE_URL_PANEL in .env"
            )
        self._base = str(cfg.remnawave_admin_panel).rstrip("/")
        self._login = cfg.remnawave_admin_login
        self._password = (
            cfg.remnawave_admin_password.get_secret_value()
            if cfg.remnawave_admin_password
            else None
        )
        self._api_key = (
            cfg.remnawave_admin_token.get_secret_value()
            if cfg.remnawave_admin_token
            else None
        )
        self._timeout = 15

    @property
    def _client(self) -> AsyncClient:
        if RemnawaveClient._session is None:
            RemnawaveClient._session = AsyncClient(timeout=self._timeout, verify=True)
        return RemnawaveClient._session

    async def _get_token(self) -> str:
        async with self._lock:
            now = datetime.now(timezone.utc)
            if self._token and self._token_expires and now < self._token_expires:
                return self._token

            if self._api_key:
                self._token = self._api_key
                RemnawaveClient._token = self._token
                RemnawaveClient._token_expires = now + timedelta(days=365)
                self._token_expires = RemnawaveClient._token_expires
                return self._token

            if not self._login or not self._password:
                raise RemnawaveAuthError("Remnawave login/password not configured")

            resp = await self._client.post(
                f"{self._base}/api/auth/login",
                json={"username": self._login, "password": self._password},
            )
            if resp.status_code != 200:
                log.warning(
                    f"Remnawave auth failed: {resp.status_code} {resp.text[:200]}"
                )
                raise RemnawaveAuthError(
                    f"Remnawave auth failed: {resp.status_code} {resp.text[:200]}"
                )
            data = resp.json()
            response = data.get("response", data)
            self._token = response["accessToken"]
            RemnawaveClient._token = self._token
            RemnawaveClient._token_expires = now + timedelta(hours=23)
            self._token_expires = RemnawaveClient._token_expires
            log.info("Remnawave token refreshed")
            return self._token

    async def _headers(self) -> dict:
        token = await self._get_token()
        return {"Authorization": f"Bearer {token}"}

    async def _request(
        self,
        method: str,
        path: str,
        *,
        suppress_statuses: Iterable[int] | None = None,
        **kwargs,
    ) -> dict | None:
        url = f"{self._base}{path}"
        suppressed = set(suppress_statuses or ())
        for attempt in range(2):
            try:
                resp = await self._client.request(
                    method, url, headers=await self._headers(), **kwargs
                )
                if resp.status_code == 401 and attempt == 0:
                    async with self._lock:
                        RemnawaveClient._token = None
                        RemnawaveClient._token_expires = None
                    continue
                if resp.status_code in suppressed:
                    return None
                resp.raise_for_status()
                data = resp.json() if resp.content else {}
                if isinstance(data, dict) and "response" in data:
                    return data["response"]
                return data
            except HTTPStatusError as e:
                log.warning(f"Remnawave {method} {path} -> {e.response.status_code}")
                raise RemnawaveRequestError(f"HTTP {e.response.status_code}")
            except RequestError as e:
                log.warning(f"Remnawave {method} {path} connection error: {e}")
                raise RemnawaveRequestError(f"Connection error: {e}")
            except Exception as e:
                log.warning(f"Remnawave {method} {path} unexpected error: {e}")
                raise RemnawaveRequestError(f"Unexpected error: {e}")
        raise RemnawaveRequestError("Max retries exceeded")

    async def get(self, path: str, params: dict = None) -> dict:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, payload: dict = None) -> dict:
        return await self._request("POST", path, json=payload or {})

    async def put(self, path: str, payload: dict = None) -> dict:
        return await self._request("PUT", path, json=payload or {})

    async def patch(self, path: str, payload: dict = None) -> dict:
        return await self._request("PATCH", path, json=payload or {})

    async def delete(self, path: str) -> None:
        await self._request("DELETE", path)


class RemnawaveService(VpnPanelInterface):
    def __init__(self) -> None:
        self._client = RemnawaveClient()

    @staticmethod
    def _coerce_int(value: object) -> int:
        if value in (None, "", False):
            return 0
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _expire_timestamp(expire_at: datetime | None) -> int | None:
        if expire_at is None:
            return None
        if expire_at.tzinfo is None:
            expire_at = expire_at.replace(tzinfo=timezone.utc)
        return int(expire_at.timestamp())

    @staticmethod
    def _parse_expire_datetime(raw_expire: object, now: datetime) -> datetime | None:
        if raw_expire is None:
            return None
        try:
            value = str(raw_expire).strip()
            if not value or value.lower() == "none":
                return None
            if value.isdigit():
                ts = int(value)
                return datetime.fromtimestamp(ts, tz=timezone.utc) if ts > 0 else now
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                ts = float(value)
                parsed = datetime.fromtimestamp(ts, tz=timezone.utc) if ts > 0 else now
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except Exception as e:
            log.warning(f"[parse_expire_datetime] parse expire error: {e}")
            return now

    async def _get_user_by_username(self, username: str) -> dict | None:
        try:
            return await self._client.get(f"/api/users/by-username/{username}")
        except RemnawaveRequestError:
            return None

    # ── System ──────────────────────────────────────────────────────────────

    async def get_system_stats(self) -> dict:
        data = await self._client.get("/api/system/stats")
        if not data:
            return {}
        result = {}
        users = data.get("users", {})
        online_stats = data.get("onlineStats", {})
        nodes = data.get("nodes", {})
        result["online_users"] = online_stats.get("onlineNow", 0)
        result["users_active"] = users.get("totalUsers", 0)
        result["total_users"] = users.get("totalUsers", 0)
        memory = data.get("memory", {})
        result["mem_used"] = memory.get("used", 0)
        cpu = data.get("cpu", {})
        result["cpu_usage"] = cpu.get("load", 0) or cpu.get("cores", 0)
        result["nodes_online"] = nodes.get("totalOnline", 0)
        return result

    async def validate_connection(self) -> bool:
        try:
            await self._client.get("/api/system/stats")
            return True
        except Exception as e:
            log.warning(f"Remnawave connection check failed: {e}")
            return False

    # ── Users ───────────────────────────────────────────────────────────────

    async def get_users(
        self, offset: int = 0, limit: int = 100, status: Optional[str] = None
    ) -> dict:
        params = {"start": offset, "size": limit}
        data = await self._client.get("/api/users", params=params)
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("users", []) or []
        else:
            items = []
        return {"users": items}

    async def get_user(self, username: str) -> Optional[dict]:
        return await self._get_user_by_username(username)

    async def create_user(
        self,
        username: str,
        expire_days: int = 30,
        data_limit_gb: int = 0,
        proxies: Optional[dict] = None,
        group_ids: Optional[list] = None,
    ) -> dict:
        import uuid

        expire_at = None
        if expire_days > 0:
            expire_at = (
                datetime.now(timezone.utc) + timedelta(days=expire_days)
            ).isoformat()

        uid = str(uuid.uuid4())
        payload: dict[str, Any] = {
            "username": username,
            "expireAt": expire_at,
            "trafficLimitBytes": data_limit_gb * 1024**3 if data_limit_gb > 0 else 0,
            "trafficLimitStrategy": "NO_RESET",
            "status": "ACTIVE",
            "vlessUuid": uid,
            "trojanPassword": uid[:16],
            "ssPassword": uid.replace("-", "")[:22],
        }

        return await self._client.post("/api/users", payload)

    async def modify_user(self, username: str, **kwargs) -> dict:
        user = await self._get_user_by_username(username)
        if not user:
            raise RemnawaveRequestError(f"User {username} not found")
        payload = {"uuid": user["uuid"], **kwargs}
        return await self._client.patch("/api/users", payload)

    async def delete_user(self, username: str) -> None:
        user = await self._get_user_by_username(username)
        if user:
            await self._client.delete(f"/api/users/{user['uuid']}")

    async def reset_user_traffic(self, username: str) -> dict:
        user = await self._get_user_by_username(username)
        if not user:
            raise RemnawaveRequestError(f"User {username} not found")
        return await self._client.post(f"/api/users/{user['uuid']}/actions/reset-traffic")

    async def revoke_user_subscription(self, username: str) -> dict:
        user = await self._get_user_by_username(username)
        if not user:
            raise RemnawaveRequestError(f"User {username} not found")
        return await self._client.post(f"/api/users/{user['uuid']}/actions/revoke")

    async def extend_user(self, username: str, extra_days: int) -> dict:
        user = await self._get_user_by_username(username)
        if not user:
            raise RemnawaveRequestError(f"User {username} not found")

        now = datetime.now(timezone.utc)
        current_expire = self._parse_expire_datetime(user.get("expireAt"), now)

        if current_expire is None or current_expire < now:
            base = now
        else:
            base = current_expire

        new_expire = (base + timedelta(days=extra_days)).isoformat()
        log.info(f"[extend_user] base={base} new_expire={new_expire}")
        return await self.modify_user(username, expireAt=new_expire)

    async def disable_user(self, username: str) -> dict:
        user = await self._get_user_by_username(username)
        if not user:
            raise RemnawaveRequestError(f"User {username} not found")
        return await self._client.post(f"/api/users/{user['uuid']}/actions/disable")

    async def enable_user(self, username: str) -> dict:
        user = await self._get_user_by_username(username)
        if not user:
            raise RemnawaveRequestError(f"User {username} not found")
        return await self._client.post(f"/api/users/{user['uuid']}/actions/enable")

    # ── Nodes ──────────────────────────────────────────────────────────────

    async def get_nodes(self) -> dict:
        data = await self._client.get("/api/nodes")
        if isinstance(data, list):
            return {"nodes": data}
        if isinstance(data, dict):
            return {"nodes": data.get("nodes", []) or []}
        return {"nodes": []}

    async def get_node_stats(self) -> dict:
        return {"nodes": []}

    async def get_node_by_id(self, node_id: int) -> dict:
        raise RemnawaveRequestError(
            "Node management is not supported in Remnawave. "
            "Use the Remnawave admin panel directly."
        )

    async def add_node(
        self,
        name: str,
        address: str,
        api_key: str,
        server_ca: str,
        connection_type: str = "grpc",
        core_config_id: int = 1,
        keep_alive: int = 60,
        port: int = 62050,
        api_port: int = 62051,
        usage_coefficient: float = 1.0,
    ) -> dict:
        raise RemnawaveRequestError(
            "Adding nodes is not supported via Remnawave API. "
            "Add nodes through the Remnawave admin panel."
        )

    async def remove_node(self, node_id: int) -> None:
        raise RemnawaveRequestError(
            "Removing nodes is not supported via Remnawave API. "
            "Remove nodes through the Remnawave admin panel."
        )

    async def reconnect_node(self, node_id: int) -> dict:
        raise RemnawaveRequestError(
            "Reconnecting nodes is not supported via Remnawave API. "
            "Use the Remnawave admin panel to manage nodes."
        )

    async def get_groups(self) -> list[dict]:
        return []

    # ── Subscription link ──────────────────────────────────────────────────

    def get_subscription_url(self, sub_token: str) -> str:
        base = str(config.remnawave.remnawave_admin_panel).rstrip("/")
        return f"{base}/sub/{sub_token}/"

    # ── Hosts (for cabinet) ────────────────────────────────────────────────

    async def get_hosts(self) -> list[dict]:
        data = await self.get_nodes()
        hosts = []
        for node in data.get("nodes", []):
            hosts.append({
                "name": node.get("name", ""),
                "address": node.get("address", ""),
                "location": node.get("countryCode", ""),
                "status": "online" if node.get("isConnected") else "offline",
            })
        return hosts

    # ── HWID (not supported in Remnawave) ──────────────────────────────────

    async def get_user_hwids(self, user_id: int) -> dict:
        return {"hwids": [], "count": 0}

    async def delete_user_hwids(self, user_id: int, hwid: str) -> None:
        pass

    async def reset_user_hwids(self, user_id: int) -> None:
        pass

    async def get_hwids_by_username(self, username: str) -> dict:
        return {"hwids": [], "count": 0}

    async def delete_hwid_from_username(self, username: str, hwid: str) -> dict:
        return {"hwids": [], "count": 0}

    async def reset_hwid_from_username(self, username: str) -> dict:
        return {"hwids": [], "count": 0}


def get_vpn_panel() -> VpnPanelInterface:
    return RemnawaveService()
