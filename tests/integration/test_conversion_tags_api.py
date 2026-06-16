from __future__ import annotations

import uuid

import pytest

pytestmark = pytest.mark.integration


def _seed_pixel(client, advertiser_id: str) -> str:
    sync = client.post(
        "/integrations/meta/sync-pixels", json={"advertiser_id": advertiser_id}
    )
    assert sync.status_code == 200
    pixels = sync.json()["pixels"]
    return pixels[0]["id"]


def test_create_conversion_tag_happy_path(client, seeded_advertiser) -> None:
    advertiser_id = seeded_advertiser["id"]
    pixel_id = _seed_pixel(client, advertiser_id)

    body = {
        "pixel_id": pixel_id,
        "name": "Purchase USD",
        "event_type": "Purchase",
        "category": "purchase",
        "value": "29.99",
        "currency": "USD",
    }
    resp = client.post(
        f"/advertisers/{advertiser_id}/conversion-tags", json=body
    )
    assert resp.status_code == 201, resp.text
    tag = resp.json()
    assert tag["status"] == "ACTIVE"
    assert tag["meta_custom_conversion_id"]

    listed = client.get(f"/advertisers/{advertiser_id}/conversion-tags").json()
    assert [t["id"] for t in listed] == [tag["id"]]


def test_create_conversion_tag_requires_currency_with_value(client, seeded_advertiser) -> None:
    advertiser_id = seeded_advertiser["id"]
    pixel_id = _seed_pixel(client, advertiser_id)

    resp = client.post(
        f"/advertisers/{advertiser_id}/conversion-tags",
        json={
            "pixel_id": pixel_id,
            "name": "x",
            "event_type": "Lead",
            "category": "lead",
            "value": "1.00",  # but no currency
        },
    )
    assert resp.status_code == 422


def test_idempotency_replay_returns_cached_response(client, seeded_advertiser) -> None:
    advertiser_id = seeded_advertiser["id"]
    pixel_id = _seed_pixel(client, advertiser_id)

    body = {
        "pixel_id": pixel_id,
        "name": "Lead",
        "event_type": "Lead",
        "category": "lead",
    }
    headers = {"Idempotency-Key": "abc-123"}
    first = client.post(
        f"/advertisers/{advertiser_id}/conversion-tags", json=body, headers=headers
    )
    second = client.post(
        f"/advertisers/{advertiser_id}/conversion-tags", json=body, headers=headers
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert second.headers.get("Idempotent-Replay") == "true"


def test_idempotency_key_rejects_changed_body(client, seeded_advertiser) -> None:
    advertiser_id = seeded_advertiser["id"]
    pixel_id = _seed_pixel(client, advertiser_id)

    headers = {"Idempotency-Key": "abc-conflict"}
    first = client.post(
        f"/advertisers/{advertiser_id}/conversion-tags",
        json={
            "pixel_id": pixel_id,
            "name": "Tag A",
            "event_type": "Lead",
            "category": "lead",
        },
        headers=headers,
    )
    assert first.status_code == 201, first.text

    second = client.post(
        f"/advertisers/{advertiser_id}/conversion-tags",
        json={
            "pixel_id": pixel_id,
            "name": "Tag B",  # changed!
            "event_type": "Lead",
            "category": "lead",
        },
        headers=headers,
    )
    assert second.status_code == 409
    assert second.json().get("code") == "idempotency_conflict"


def test_create_conversion_tag_404_for_unknown_advertiser(client) -> None:
    resp = client.post(
        f"/advertisers/{uuid.uuid4()}/conversion-tags",
        json={
            "pixel_id": str(uuid.uuid4()),
            "name": "x",
            "event_type": "Lead",
            "category": "lead",
        },
    )
    assert resp.status_code == 404
