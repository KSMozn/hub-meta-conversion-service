"""Idempotency-Key support for unsafe endpoints.

Semantics:
* First request stores (endpoint, key, request_hash) -> (status, body).
* Replay with same key + body: return the cached response verbatim.
* Replay with same key + different body: 409 Conflict (the classic footgun).
* TTL is short — 24h is enough for retry storms; longer just keeps stale data.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.idempotency import IdempotencyRepository
from app.services.exceptions import ConflictError

_DEFAULT_TTL = timedelta(hours=24)


class IdempotencyConflictError(ConflictError):
    """Same key replayed with a different request body."""


def hash_request(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class IdempotencyService:
    def __init__(self, session: Session) -> None:
        self.repo = IdempotencyRepository(session)

    def lookup(
        self, *, endpoint: str, key: str, request_hash: str
    ) -> tuple[int, dict] | None:
        existing = self.repo.get(endpoint, key)
        if existing is None:
            return None
        if existing.request_hash != request_hash:
            raise IdempotencyConflictError(
                "Idempotency-Key reused with a different request body"
            )
        return existing.response_status, existing.response_body

    def store(
        self,
        *,
        endpoint: str,
        key: str,
        request_hash: str,
        status_code: int,
        response_body: dict,
        ttl: timedelta = _DEFAULT_TTL,
    ) -> None:
        self.repo.insert(
            endpoint=endpoint,
            key=key,
            request_hash=request_hash,
            response_status=status_code,
            response_body=response_body,
            expires_at=datetime.now(timezone.utc) + ttl,
        )
