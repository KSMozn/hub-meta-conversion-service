"""Engine and session factory.

Two flavours:
* the long-lived engine created from settings at startup, and
* a per-request ``Session`` exposed as a FastAPI dependency.

Tests build their own engine pointing at a testcontainer Postgres, so the engine
is intentionally instantiable from any URL rather than hidden behind a global.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings


def build_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
        future=True,
    )


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _ensure_factory() -> sessionmaker[Session]:
    global _engine, _session_factory
    if _session_factory is None:
        settings = get_settings()
        _engine = build_engine(settings)
        _session_factory = build_session_factory(_engine)
    return _session_factory


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields a transactional session per request."""
    factory = _ensure_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_session_factory() -> None:
    """For tests: drop the cached engine/factory so the next call rebuilds them."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
