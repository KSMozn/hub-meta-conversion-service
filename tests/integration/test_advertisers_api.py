from __future__ import annotations

import uuid

import pytest

pytestmark = pytest.mark.integration


def test_create_advertiser_returns_201_and_persists(client) -> None:
    resp = client.post(
        "/advertisers",
        json={
            "name": "Test Co",
            "external_ref": "ext-001",
            "meta_business_id": "biz_1",
            "meta_ad_account_id": "act_1",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "Test Co"
    uuid.UUID(body["id"])

    got = client.get(f"/advertisers/{body['id']}")
    assert got.status_code == 200
    assert got.json()["external_ref"] == "ext-001"


def test_create_advertiser_conflicts_on_duplicate_external_ref(client) -> None:
    payload = {"name": "Co", "external_ref": "ext-duplicate"}
    assert client.post("/advertisers", json=payload).status_code == 201
    second = client.post("/advertisers", json=payload)
    assert second.status_code == 409


def test_get_advertiser_404(client) -> None:
    resp = client.get(f"/advertisers/{uuid.uuid4()}")
    assert resp.status_code == 404
