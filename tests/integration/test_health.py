import pytest

pytestmark = pytest.mark.integration


def test_healthz(client) -> None:
    assert client.get("/healthz").json() == {"status": "ok"}


def test_readyz(client) -> None:
    assert client.get("/readyz").json() == {"status": "ready"}
