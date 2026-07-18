import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.cabinet import views as cabinet_views
from app.api.dependencies import get_db
from app.bot.handlers import payments as bot_payments
from app.bot.middlewares import user_notify as user_notify_middleware
from app.models.bot_settings import BotSettings
from app.models.payment import Payment, PaymentProvider, PaymentStatus, PaymentType
from app.models.promo import PromoCode, PromoType
from app.models.promo_usage import PromoUsage
from app.services import encryption as encryption_service
from app.services.bot_settings import BotSettingsService
from app.services.plan import PlanService
from app.services.platega import PlategaService


@pytest.fixture
async def cabinet_client(session, sample_user, monkeypatch):
    app = FastAPI()
    app.include_router(cabinet_views.router)

    async def override_get_db():
        yield session

    async def fake_require_active_user(request, db):
        return sample_user

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(cabinet_views, "_require_active_user", fake_require_active_user)

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="https://testserver"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_cabinet_promo_days_creates_subscription_without_existing_key(
    cabinet_client, session, sample_user, monkeypatch
):
    promo = PromoCode(
        code="DAYSWELCOME",
        promo_type=PromoType.DAYS.value,
        value=Decimal("5.00"),
        max_uses=1,
        current_uses=0,
        is_active=True,
    )
    session.add(promo)
    await session.commit()

    expires_at = datetime.now(timezone.utc) + timedelta(days=5)

    async def fake_provision_days(
        self, user_id: int, days: int, name: str | None = None
    ):
        assert user_id == sample_user.id
        assert days == 5
        assert name == "Промокод — DAYSWELCOME"
        return SimpleNamespace(
            access_url="https://vpn.example/new-key", expires_at=expires_at
        )

    monkeypatch.setattr(
        cabinet_views.VpnKeyService, "provision_days", fake_provision_days
    )

    response = await cabinet_client.post(
        "/cabinet/promo/apply", data={"code": "DAYSWELCOME"}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["access_url"] == "https://vpn.example/new-key"
    assert "создана" in payload["message"]

    usage = await session.execute(
        select(PromoUsage).where(
            PromoUsage.promo_id == promo.id,
            PromoUsage.user_id == sample_user.id,
        )
    )
    assert usage.scalar_one_or_none() is not None


def test_platega_status_helpers_cover_documented_and_common_variants():
    assert PlategaService.is_success_status("CONFIRMED") is True
    assert PlategaService.is_success_status("confirmed") is True
    assert PlategaService.is_success_status("paid") is True
    assert PlategaService.is_failure_status("CANCELED") is True
    assert PlategaService.is_failure_status("cancelled") is True
    assert PlategaService.is_failure_status("CHARGEBACKED") is True


def test_encryption_accepts_valid_fernet_key(monkeypatch):
    key = encryption_service.generate_key()
    monkeypatch.setenv("ENCRYPTION_KEY", key)
    monkeypatch.setattr(encryption_service, "_FERNET", None)
    monkeypatch.setattr(encryption_service, "_MASTER_KEY", None)

    encrypted = encryption_service.encrypt_value("secret-value")

    assert encryption_service.decrypt_value(encrypted) == "secret-value"
    assert encryption_service.get_encryption_key_info().startswith("Configured")


def test_encryption_falls_back_without_crashing_on_invalid_key(monkeypatch):
    monkeypatch.setenv("ENCRYPTION_KEY", "!" * 44)
    monkeypatch.setattr(encryption_service, "_FERNET", None)
    monkeypatch.setattr(encryption_service, "_MASTER_KEY", None)

    encrypted = encryption_service.encrypt_value("safe-fallback")

    assert encryption_service.decrypt_value(encrypted) == "safe-fallback"
    assert encryption_service.get_encryption_key_info().startswith("Auto-generated")


@pytest.mark.asyncio
async def test_bot_settings_encrypts_yookassa_secret_override(session):
    service = BotSettingsService(session)

    await service.set("yookassa_secret_key_override", "yk-secret-value")
    await session.commit()

    row = (
        await session.execute(
            select(BotSettings).where(BotSettings.key == "yookassa_secret_key_override")
        )
    ).scalar_one()

    assert row.value != "yk-secret-value"
    assert await service.get("yookassa_secret_key_override") == "yk-secret-value"


def test_user_notify_prunes_stale_cache_entries():
    now = time.time()
    cache = {
        user_id: now - (user_notify_middleware._EXPIRED_COOLDOWN * 10)
        for user_id in range(user_notify_middleware._NOTIFY_CACHE_PRUNE_THRESHOLD)
    }
    cache[user_notify_middleware._NOTIFY_CACHE_PRUNE_THRESHOLD + 1] = now - 60

    user_notify_middleware._prune_notification_cache(
        cache,
        now,
        user_notify_middleware._EXPIRED_COOLDOWN,
    )

    assert 1 not in cache
    assert user_notify_middleware._NOTIFY_CACHE_PRUNE_THRESHOLD + 1 in cache


@pytest.mark.asyncio
async def test_bot_provision_and_notify_sends_fallback_message_when_key_not_ready(
    session, sample_user, sample_plan, monkeypatch
):
    payment = Payment(
        user_id=sample_user.id,
        provider=PaymentProvider.YOOKASSA.value,
        payment_type=PaymentType.SUBSCRIPTION.value,
        amount=sample_plan.price,
        currency="RUB",
        status=PaymentStatus.SUCCEEDED.value,
        external_id="yk_ready_later",
    )
    session.add(payment)
    await session.commit()

    class _SessionCtx:
        def __init__(self, db_session):
            self._db_session = db_session

        async def __aenter__(self):
            return self._db_session

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _Bot:
        def __init__(self):
            self.messages: list[tuple[int, str]] = []

        async def send_message(self, chat_id, text, parse_mode="HTML"):
            self.messages.append((chat_id, text))

    async def fake_get_all(self):
        return {}

    async def fake_provision(self, user_id: int, plan):
        return None

    monkeypatch.setattr(
        bot_payments, "AsyncSessionFactory", lambda: _SessionCtx(session)
    )
    monkeypatch.setattr(bot_payments.BotSettingsService, "get_all", fake_get_all)
    monkeypatch.setattr(bot_payments.VpnKeyService, "provision", fake_provision)

    bot = _Bot()
    ok = await bot_payments._provision_and_notify(
        sample_user.id,
        payment.id,
        sample_plan.id,
        bot,
        force_notify=True,
    )

    assert ok is True
    assert bot.messages
    assert "готовится" in bot.messages[0][1]


@pytest.mark.asyncio
async def test_plan_service_update_allows_clearing_description(session, sample_plan):
    updated = await PlanService(session).update(
        sample_plan.id,
        name="Updated Plan",
        description=None,
    )
    await session.commit()

    assert updated is not None
    assert updated.name == "Updated Plan"
    assert updated.description is None
