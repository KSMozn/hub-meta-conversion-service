from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.idempotency import IdempotencyRecord


class IdempotencyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, endpoint: str, key: str) -> IdempotencyRecord | None:
        stmt = select(IdempotencyRecord).where(
            IdempotencyRecord.endpoint == endpoint,
            IdempotencyRecord.key == key,
        )
        return self.session.scalar(stmt)

    def insert(
        self,
        *,
        endpoint: str,
        key: str,
        request_hash: str,
        response_status: int,
        response_body: dict,
        expires_at: datetime,
    ) -> IdempotencyRecord:
        record = IdempotencyRecord(
            endpoint=endpoint,
            key=key,
            request_hash=request_hash,
            response_status=response_status,
            response_body=response_body,
            expires_at=expires_at,
        )
        self.session.add(record)
        try:
            self.session.flush()
        except IntegrityError:
            # Another concurrent request stored the same key first; re-read.
            self.session.rollback()
            existing = self.get(endpoint, key)
            assert existing is not None
            return existing
        return record
