from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_pixel_sync_service
from app.schemas.pixel import PixelOut, PixelSyncRequest, PixelSyncResult
from app.services.pixel_sync_service import PixelSyncService

router = APIRouter(prefix="/integrations/meta", tags=["integrations"])


@router.post("/sync-pixels", response_model=PixelSyncResult)
def sync_pixels(
    payload: PixelSyncRequest,
    service: PixelSyncService = Depends(get_pixel_sync_service),
) -> PixelSyncResult:
    pixels, created, updated = service.sync_for_advertiser(payload.advertiser_id)
    return PixelSyncResult(
        advertiser_id=payload.advertiser_id,
        pixels_fetched=created + updated,
        pixels_created=created,
        pixels_updated=updated,
        pixels=[PixelOut.model_validate(p) for p in pixels],
    )
