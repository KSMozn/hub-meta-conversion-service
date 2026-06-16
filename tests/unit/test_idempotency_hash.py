from app.services.idempotency import hash_request


def test_hash_stable_for_key_order() -> None:
    a = {"a": 1, "b": 2, "nested": {"x": 1, "y": 2}}
    b = {"nested": {"y": 2, "x": 1}, "b": 2, "a": 1}
    assert hash_request(a) == hash_request(b)


def test_hash_changes_on_value_change() -> None:
    assert hash_request({"a": 1}) != hash_request({"a": 2})
