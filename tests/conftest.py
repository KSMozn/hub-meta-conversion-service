"""Pytest fixtures.

* ``postgres_url`` is session-scoped and boots a real Postgres container via
  testcontainers. Tests that need DB integration depend on it.
* ``db_session`` gives a clean per-test transaction that rolls back on teardown.
* ``client`` builds a fresh FastAPI app per test with the test DB and a fresh
  ``MockMetaAdapter`` so cases never see each other's seeded state.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import models  # noqa: F401 - register metadata
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_session
from app.integrations.meta.mock_adapter import MockMetaAdapter
from app.integrations.meta.schemas import MetaPixel
from app.main import create_app
from app.services.oauth_service import OAuthService


def _have_docker() -> bool:
    try:
        import docker  # type: ignore[import-untyped]

        docker.from_env().ping()
        return True
    except Exception:
        return False


_DOCKER_AVAILABLE = _have_docker()


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    if not _DOCKER_AVAILABLE:
        pytest.skip("docker not available; skipping testcontainers-based tests")
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:16-alpine") as pg:
        # testcontainers default driver is psycopg2; we use psycopg3.
        url = pg.get_connection_url().replace("postgresql+psycopg2", "postgresql+psycopg")
        yield url


@pytest.fixture(scope="session")
def engine(postgres_url: str) -> Iterator[Engine]:
    eng = create_engine(postgres_url, future=True)
    Base.metadata.create_all(eng)
    try:
        yield eng
    finally:
        Base.metadata.drop_all(eng)
        eng.dispose()


@pytest.fixture()
def db_session(engine: Engine) -> Iterator[Session]:
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        # Hard reset between tests.
        session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()


@pytest.fixture()
def settings(monkeypatch: pytest.MonkeyPatch, postgres_url: str) -> Settings:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", postgres_url)
    monkeypatch.setenv("META_USE_MOCK", "true")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", "test-key-test-key-test-key-test-key=")
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture()
def meta_adapter() -> MockMetaAdapter:
    return MockMetaAdapter()


@pytest.fixture()
def client(
    settings: Settings,
    engine: Engine,
    db_session: Session,
    meta_adapter: MockMetaAdapter,
) -> Iterator[TestClient]:
    # Bind the request-scoped session to the same engine the test uses.
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    def override_get_session() -> Iterator[Session]:
        s = factory()
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    app = create_app(settings=settings, meta_adapter=meta_adapter)
    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def seeded_advertiser(client: TestClient, meta_adapter: MockMetaAdapter, db_session: Session) -> dict:
    """Create an advertiser + OAuth token + one Meta pixel ready for the API."""
    settings = get_settings()
    resp = client.post(
        "/advertisers",
        json={
            "name": "Acme Corp",
            "external_ref": f"acme-{uuid.uuid4()}",
            "meta_business_id": "biz_123",
            "meta_ad_account_id": "act_42",
        },
    )
    assert resp.status_code == 201, resp.text
    advertiser = resp.json()
    advertiser_id = uuid.UUID(advertiser["id"])

    OAuthService(db_session, settings).store_initial_token(
        advertiser_id=advertiser_id,
        access_token="initial-access-token",
        refresh_token="initial-refresh-token",
        ttl=timedelta(hours=1),
    )
    db_session.commit()

    meta_adapter.seed_pixels(
        "act_42",
        [
            MetaPixel(id="pix_aaa", name="Website Pixel", status="ACTIVE"),
            MetaPixel(id="pix_bbb", name="App Pixel", status="ACTIVE"),
        ],
    )
    return advertiser


# Allow CI to opt out of docker-dependent tests cleanly.
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if _DOCKER_AVAILABLE or os.environ.get("RUN_INTEGRATION"):
        return
    skip_marker = pytest.mark.skip(reason="docker not available; install Docker to run integration tests")
    for item in items:
        if "postgres_url" in getattr(item, "fixturenames", ()):
            item.add_marker(skip_marker)
