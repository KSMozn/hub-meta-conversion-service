from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import get_advertiser_service, get_conversion_tag_service, get_pixel_sync_service
from app.schemas.advertiser import AdvertiserCreate, AdvertiserOut
from app.schemas.conversion_tag import ConversionTagOut
from app.schemas.pixel import PixelOut
from app.services.advertiser_service import AdvertiserService
from app.services.conversion_tag_service import ConversionTagService
from app.services.pixel_sync_service import PixelSyncService

router = APIRouter(prefix="/advertisers", tags=["advertisers"])


@router.post(
    "",
    response_model=AdvertiserOut,
    status_code=status.HTTP_201_CREATED,
)
def create_advertiser(
    payload: AdvertiserCreate,
    service: AdvertiserService = Depends(get_advertiser_service),
) -> AdvertiserOut:
    advertiser = service.create(payload)
    return AdvertiserOut.model_validate(advertiser)


@router.get("/{advertiser_id}", response_model=AdvertiserOut)
def get_advertiser(
    advertiser_id: uuid.UUID,
    service: AdvertiserService = Depends(get_advertiser_service),
) -> AdvertiserOut:
    return AdvertiserOut.model_validate(service.get(advertiser_id))


@router.get("/{advertiser_id}/pixels", response_model=list[PixelOut])
def list_pixels(
    advertiser_id: uuid.UUID,
    advertiser_service: AdvertiserService = Depends(get_advertiser_service),
    sync_service: PixelSyncService = Depends(get_pixel_sync_service),
) -> list[PixelOut]:
    advertiser_service.get(advertiser_id)  # 404 if missing
    pixels = sync_service.pixels.list_for_advertiser(advertiser_id)
    return [PixelOut.model_validate(p) for p in pixels]


@router.get(
    "/{advertiser_id}/conversion-tags",
    response_model=list[ConversionTagOut],
)
def list_conversion_tags(
    advertiser_id: uuid.UUID,
    service: ConversionTagService = Depends(get_conversion_tag_service),
) -> list[ConversionTagOut]:
    tags = service.list_for_advertiser(advertiser_id)
    return [ConversionTagOut.model_validate(t) for t in tags]
