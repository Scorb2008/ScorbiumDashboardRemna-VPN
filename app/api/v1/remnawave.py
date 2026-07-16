"""Remnawave API proxy — forwards any request to the Remnawave panel API."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from httpx import AsyncClient
from app.api.dependencies import get_current_admin
from app.services.remnawave.remnawave_api import RemnawaveClient

router = APIRouter()


async def _proxy(path: str, method: str, request: Request) -> Response:
    """Forward request to Remnawave API."""
    try:
        client = RemnawaveClient()
        headers = await client._headers()
        headers.pop("content-length", None)

        body = await request.body()
        url = f"{client._base}/{path.lstrip('/')}"

        async with AsyncClient(timeout=30) as session:
            resp = await session.request(
                method,
                url,
                headers=headers,
                content=body or None,
                params=dict(request.query_params),
            )

        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers={k: v for k, v in resp.headers.items()
                     if k.lower() not in ("content-encoding", "transfer-encoding", "content-length", "server")},
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Remnawave proxy error: {str(e)}")


@router.api_route("/proxy/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_to_remnawave(
    path: str,
    request: Request,
    _admin=Depends(get_current_admin),
):
    return await _proxy(path, request.method, request)


@router.get("/status")
async def remnawave_status(_admin=Depends(get_current_admin)):
    try:
        client = RemnawaveClient()
        headers = await client._headers()
        async with AsyncClient(timeout=15) as session:
            resp = await session.get(f"{client._base}/api/system/stats", headers=headers)
            if resp.status_code == 200:
                return {"connected": True, "stats": resp.json()}
            return {"connected": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"connected": False, "error": str(e)}


@router.get("/nodes")
async def remnawave_nodes(_admin=Depends(get_current_admin)):
    try:
        client = RemnawaveClient()
        headers = await client._headers()
        async with AsyncClient(timeout=15) as session:
            resp = await session.get(f"{client._base}/api/nodes", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("nodes", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            return []
    except Exception:
        return []


@router.get("/users")
async def remnawave_users(request: Request, _admin=Depends(get_current_admin)):
    try:
        client = RemnawaveClient()
        headers = await client._headers()
        limit = request.query_params.get("limit", "100")
        offset = request.query_params.get("offset", "0")
        async with AsyncClient(timeout=15) as session:
            resp = await session.get(
                f"{client._base}/api/users?start={offset}&size={limit}",
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("users", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            return []
    except Exception:
        return []
