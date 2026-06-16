"""FastAPI application factory.

The factory pattern keeps tests honest: each test gets its own app instance
with its own state (DB engine, Meta adapter), so global state never leaks
between cases.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.routes import advertisers, conversion_tags, health, integrations
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.integrations.meta.adapter import MetaAdapter
from app.integrations.meta.client import MetaApiClient
from app.integrations.meta.mock_adapter import MockMetaAdapter
from app.integrations.meta.real_adapter import RealMetaAdapter


def _build_default_adapter(settings: Settings) -> MetaAdapter:
    if settings.meta_use_mock:
        return MockMetaAdapter(
            rate_limit_every=settings.meta_mock_rate_limit_every,
            fail_rate=settings.meta_mock_fail_rate,
        )
    client = MetaApiClient(settings)
    return RealMetaAdapter(client)


def create_app(
    *,
    settings: Settings | None = None,
    meta_adapter: MetaAdapter | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):  # noqa: ANN001
        app.state.meta_adapter = meta_adapter or _build_default_adapter(settings)
        app.state.settings = settings
        try:
            yield
        finally:
            adapter = app.state.meta_adapter
            if isinstance(adapter, RealMetaAdapter):
                # RealMetaAdapter owns an httpx.Client via MetaApiClient
                adapter._client.close()  # type: ignore[attr-defined]

    app = FastAPI(
        title="Hub Meta Conversion Service",
        version="0.1.0",
        lifespan=lifespan,
    )
    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(advertisers.router)
    app.include_router(integrations.router)
    app.include_router(conversion_tags.router)
    return app


app = create_app()
