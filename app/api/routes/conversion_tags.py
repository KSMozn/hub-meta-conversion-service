from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status

from app.api.deps import get_conversion_tag_service, get_idempotency_service
from app.schemas.conversion_tag import ConversionTagCreate, ConversionTagOut
from app.services.conversion_tag_service import ConversionTagService
from app.services.idempotency import IdempotencyService, hash_request

router = APIRouter(prefix="/advertisers/{advertiser_id}/conversion-tags", tags=["conversion-tags"])

_ENDPOINT = "POST /advertisers/{id}/conversion-tags"


@router.post(
    "",
    response_model=ConversionTagOut,
    status_code=status.HTTP_201_CREATED,
)
def create_conversion_tag(
    advertiser_id: uuid.UUID,
    payload: ConversionTagCreate,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    service: ConversionTagService = Depends(get_conversion_tag_service),
    idem: IdempotencyService = Depends(get_idempotency_service),
) -> ConversionTagOut:
    request_hash = hash_request(
        {"advertiser_id": str(advertiser_id), **payload.model_dump(mode="json")}
    )

    if idempotency_key:
        cached = idem.lookup(
            endpoint=_ENDPOINT, key=idempotency_key, request_hash=request_hash
        )
        if cached is not None:
            cached_status, cached_body = cached
            response.status_code = cached_status
            response.headers["Idempotent-Replay"] = "true"
            # FastAPI will skip response_model serialization since we return the
            # cached dict via Response semantics. Use the same shape.
            return ConversionTagOut.model_validate(cached_body)

    tag = service.create(advertiser_id, payload)
    out = ConversionTagOut.model_validate(tag)

    if idempotency_key:
        try:
            idem.store(
                endpoint=_ENDPOINT,
                key=idempotency_key,
                request_hash=request_hash,
                status_code=status.HTTP_201_CREATED,
                response_body=out.model_dump(mode="json"),
            )
        except Exception as exc:  # pragma: no cover - defensive
            # Failure to persist the idempotency record must not fail the request,
            # but we surface it so retries don't silently double-bill.
            raise HTTPException(status_code=500, detail=f"idempotency store failed: {exc}")

    return out
