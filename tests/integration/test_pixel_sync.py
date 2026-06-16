from __future__ import annotations

import pytest

from app.integrations.meta.schemas import MetaPixel

pytestmark = pytest.mark.integration


def test_sync_pixels_creates_then_updates(client, seeded_advertiser, meta_adapter) -> None:
    advertiser_id = seeded_advertiser["id"]

    first = client.post(
        "/integrations/meta/sync-pixels", json={"advertiser_id": advertiser_id}
    )
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["pixels_created"] == 2
    assert body["pixels_updated"] == 0

    # Rename a pixel on the Meta side and resync -> should be reported as updated.
    meta_adapter.seed_pixels(
        "act_42",
        [
            MetaPixel(id="pix_aaa", name="Website Pixel v2", status="ACTIVE"),
            MetaPixel(id="pix_bbb", name="App Pixel", status="PAUSED"),
        ],
    )
    second = client.post(
        "/integrations/meta/sync-pixels", json={"advertiser_id": advertiser_id}
    )
    assert second.status_code == 200, second.text
    body = second.json()
    assert body["pixels_created"] == 0
    assert body["pixels_updated"] == 2

    listed = client.get(f"/advertisers/{advertiser_id}/pixels").json()
    by_meta_id = {p["meta_pixel_id"]: p for p in listed}
    assert by_meta_id["pix_aaa"]["name"] == "Website Pixel v2"
    assert by_meta_id["pix_bbb"]["status"] == "PAUSED"
