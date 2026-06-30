from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.remnawave.remnawave_api import RemnawaveService
from app.services.vpn_key import VpnKeyService
from app.models.vpn_key import VpnKeyStatus


@pytest.mark.asyncio
async def test_remnawave_create_user_sends_iso_expire():
    service = RemnawaveService.__new__(RemnawaveService)
    post_mock = AsyncMock(return_value={"username": "vpn_1_1", "subscriptionUrl": "https://panel.example/sub/uuid/"})
    service._client = SimpleNamespace(post=post_mock)

    before = datetime.now(timezone.utc)
    await service.create_user("vpn_1_1", expire_days=30)
    after = datetime.now(timezone.utc)

    _, payload = post_mock.call_args[0]
    expire_at_str = payload["expireAt"]
    expire_at = datetime.fromisoformat(expire_at_str.replace("Z", "+00:00"))

    assert before + timedelta(days=30) <= expire_at <= after + timedelta(days=30)


@pytest.mark.asyncio
async def test_remnawave_extend_user_preserves_future_expiry():
    service = RemnawaveService.__new__(RemnawaveService)
    now = datetime.now(timezone.utc)
    future_expire = now + timedelta(days=10)

    service._get_user_by_username = AsyncMock(return_value={
        "uuid": "test-uuid",
        "username": "vpn_1_1",
        "expireAt": future_expire.isoformat(),
    })
    service.modify_user = AsyncMock(return_value={"username": "vpn_1_1"})
    service._client = SimpleNamespace(patch=AsyncMock())

    await service.extend_user("vpn_1_1", 7)

    expected_new_expire = future_expire + timedelta(days=7)
    service.modify_user.assert_awaited_once_with(
        "vpn_1_1",
        expireAt=expected_new_expire.isoformat(),
    )


@pytest.mark.asyncio
async def test_refresh_traffic_for_keys_uses_remnawave_payload(
    session, sample_vpn_key
):
    service = VpnKeyService(session)
    service._traffic_columns_supported = True
    panel = AsyncMock()
    panel.get_user.return_value = {
        "username": sample_vpn_key.remnawave_key_id,
        "subscriptionUrl": "https://panel.example/sub/uuid/",
        "shortUuid": "abc",
        "userTraffic": {"usedTrafficBytes": 222},
        "status": "ACTIVE",
        "expireAt": sample_vpn_key.expires_at.isoformat(),
    }
    service._panel = panel

    await service.refresh_traffic_for_keys([sample_vpn_key])

    assert sample_vpn_key.download == 222
    assert sample_vpn_key.upload == 0
    panel.get_user.assert_awaited_once_with(sample_vpn_key.remnawave_key_id)


@pytest.mark.asyncio
async def test_extend_keeps_local_expiry_unchanged_when_remnawave_fails(
    session, sample_vpn_key
):
    service = VpnKeyService(session)
    panel = AsyncMock()
    panel.extend_user.side_effect = RuntimeError("panel unavailable")
    service._panel = panel
    before = sample_vpn_key.expires_at

    result = await service.extend(sample_vpn_key.id, 7)

    assert result is None
    assert sample_vpn_key.expires_at == before


@pytest.mark.asyncio
async def test_refresh_traffic_for_keys_updates_stale_status_from_remnawave(
    session, sample_vpn_key
):
    service = VpnKeyService(session)
    service._traffic_columns_supported = True
    sample_vpn_key.status = VpnKeyStatus.REVOKED.value

    panel = AsyncMock()
    panel.get_user.return_value = {
        "username": sample_vpn_key.remnawave_key_id,
        "status": "ACTIVE",
        "subscriptionUrl": "https://panel.example/sub/uuid/",
        "userTraffic": {"usedTrafficBytes": 1},
        "expireAt": sample_vpn_key.expires_at.isoformat(),
    }
    service._panel = panel

    await service.refresh_traffic_for_keys([sample_vpn_key])

    assert sample_vpn_key.status == VpnKeyStatus.ACTIVE.value


@pytest.mark.asyncio
async def test_sync_from_remnawave_maps_normalized_remnawave_traffic(
    session, sample_vpn_key
):
    service = VpnKeyService(session)
    service._traffic_columns_supported = True
    panel = AsyncMock()
    panel.get_user.return_value = {
        "username": sample_vpn_key.remnawave_key_id,
        "subscriptionUrl": "https://panel.example/sub/uuid/",
        "status": "ACTIVE",
        "expireAt": sample_vpn_key.expires_at.isoformat(),
        "userTraffic": {
            "usedTrafficBytes": 4096,
        },
    }
    service._panel = panel

    result = await service.sync_from_remnawave()

    assert result == {"synced": 1, "errors": 0, "fixed_expire": 0}
    assert sample_vpn_key.download == 4096
    assert sample_vpn_key.upload == 0


@pytest.mark.asyncio
async def test_sync_from_remnawave_repairs_expire(
    session, sample_vpn_key
):
    service = VpnKeyService(session)
    service._traffic_columns_supported = False
    original_expire = sample_vpn_key.expires_at
    panel_expire = sample_vpn_key.expires_at - timedelta(days=2)

    panel = AsyncMock()
    panel.get_user.return_value = {
        "username": sample_vpn_key.remnawave_key_id,
        "status": "ACTIVE",
        "expireAt": panel_expire.astimezone(timezone.utc).isoformat(),
    }
    panel.modify_user = AsyncMock(return_value={"username": sample_vpn_key.remnawave_key_id})
    service._panel = panel

    result = await service.sync_from_remnawave()

    assert result == {"synced": 1, "errors": 0, "fixed_expire": 1}
    assert service._expire_timestamp(sample_vpn_key.expires_at) == service._expire_timestamp(
        panel_expire
    )
    assert sample_vpn_key.expires_at != original_expire
    panel.modify_user.assert_not_awaited()
