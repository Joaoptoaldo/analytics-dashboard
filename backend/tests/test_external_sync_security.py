import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.db import SessionLocal
from backend.models.sync_state import SyncState
from backend.routers import external_sync


def _build_request(headers: dict[str, str] | None = None, host: str = "127.0.0.1") -> Request:
    encoded_headers = []
    for key, value in (headers or {}).items():
        encoded_headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/external-products/sync",
        "raw_path": b"/api/external-products/sync",
        "query_string": b"",
        "headers": encoded_headers,
        "client": (host, 12345),
        "server": ("testserver", 80),
    }
    return Request(scope)


@pytest.fixture(autouse=True)
def _reset_rate_limit_state():
    db = SessionLocal()
    try:
        db.query(SyncState).delete()
        db.commit()
        yield
        db.query(SyncState).delete()
        db.commit()
    finally:
        db.close()


def test_sync_access_blocks_when_token_not_configured(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("EXTERNAL_SYNC_TOKEN", raising=False)
    request = _build_request()

    with pytest.raises(HTTPException) as error:
        external_sync._enforce_sync_access(request)

    assert error.value.status_code == 500


def test_sync_access_rejects_invalid_token(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("EXTERNAL_SYNC_TOKEN", "expected-token")
    request = _build_request(headers={"x-internal-token": "wrong-token"})

    with pytest.raises(HTTPException) as error:
        external_sync._enforce_sync_access(request)

    assert error.value.status_code == 401


def test_sync_access_accepts_valid_token(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("EXTERNAL_SYNC_TOKEN", "expected-token")
    request = _build_request(headers={"x-internal-token": "expected-token"})
    external_sync._enforce_sync_access(request)


def test_sync_rate_limit_blocks_second_immediate_request(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("EXTERNAL_SYNC_MIN_INTERVAL_SECONDS", "60")
    request = _build_request(host="10.0.0.7")

    external_sync._enforce_sync_rate_limit(request)

    with pytest.raises(HTTPException) as error:
        external_sync._enforce_sync_rate_limit(request)

    assert error.value.status_code == 429


def test_sync_rate_limit_disabled_when_zero(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("EXTERNAL_SYNC_MIN_INTERVAL_SECONDS", "0")
    request = _build_request(host="10.0.0.8")
    external_sync._enforce_sync_rate_limit(request)
    external_sync._enforce_sync_rate_limit(request)
