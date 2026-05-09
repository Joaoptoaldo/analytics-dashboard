import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend import config as cfg
from backend.routers import external_sync


def _build_request(headers: dict[str, str] | None = None, host: str = "127.0.0.1") -> Request:
    encoded_headers = []
    for key, value in (headers or {}).items():
        encoded_headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": "/internal/external-products/sync",
        "raw_path": b"/internal/external-products/sync",
        "query_string": b"",
        "headers": encoded_headers,
        "client": (host, 54321),
        "server": ("testserver", 80),
    }
    return Request(scope)


@pytest.mark.parametrize("vercel_host", ["vercel.app", "vercel.com", "dummy.vercel.app"])
def test_vercel_calls_require_token_in_prod(monkeypatch: pytest.MonkeyPatch, vercel_host: str):
    # Simula backend em PROD (não development) e sem ALLOW_LOCAL_SYNC
    monkeypatch.setattr(cfg, "IS_DEVELOPMENT", False)
    monkeypatch.setattr(cfg, "ALLOW_LOCAL_SYNC", False)
    # external_sync imported frozen values at module import time; patch them too
    monkeypatch.setattr(external_sync, "IS_DEVELOPMENT", False)
    monkeypatch.setattr(external_sync, "ALLOW_LOCAL_SYNC", False)

    # Sem token configurado -> 500
    monkeypatch.setattr(cfg, "EXTERNAL_SYNC_TOKEN", None)
    monkeypatch.setattr(external_sync, "EXTERNAL_SYNC_TOKEN", None)
    req = _build_request(host=vercel_host)
    with pytest.raises(HTTPException) as exc:
        external_sync._enforce_sync_access(req)
    assert exc.value.status_code == 500

    # Com token configurado mas cabeçalho inválido -> 401
    monkeypatch.setattr(cfg, "EXTERNAL_SYNC_TOKEN", "expected-token")
    monkeypatch.setattr(external_sync, "EXTERNAL_SYNC_TOKEN", "expected-token")
    req = _build_request(headers={"x-internal-token": "wrong"}, host=vercel_host)
    with pytest.raises(HTTPException) as exc2:
        external_sync._enforce_sync_access(req)
    assert exc2.value.status_code == 401

    # Com token válido -> permitido
    req = _build_request(headers={"x-internal-token": "expected-token"}, host=vercel_host)
    external_sync._enforce_sync_access(req)


def test_local_dev_allows_without_token_when_allow_local_true(monkeypatch: pytest.MonkeyPatch):
    # Simular ambiente de desenvolvimento com ALLOW_LOCAL_SYNC habilitado
    monkeypatch.setattr(cfg, "IS_DEVELOPMENT", True)
    monkeypatch.setattr(cfg, "ALLOW_LOCAL_SYNC", True)
    monkeypatch.setattr(cfg, "EXTERNAL_SYNC_TOKEN", None)
    monkeypatch.setattr(external_sync, "IS_DEVELOPMENT", True)
    monkeypatch.setattr(external_sync, "ALLOW_LOCAL_SYNC", True)
    monkeypatch.setattr(external_sync, "EXTERNAL_SYNC_TOKEN", None)

    # Loopback host deve ser permitido sem token
    req = _build_request(host="127.0.0.1")
    external_sync._enforce_sync_access(req)


def test_local_dev_skips_rate_limit_when_allow_local_true(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(cfg, "IS_DEVELOPMENT", True)
    monkeypatch.setattr(cfg, "ALLOW_LOCAL_SYNC", True)
    monkeypatch.setattr(external_sync, "IS_DEVELOPMENT", True)
    monkeypatch.setattr(external_sync, "ALLOW_LOCAL_SYNC", True)

    # Mesmo com intervalo padrão, chamadas locais não devem ser rate-limited
    req = _build_request(host="127.0.0.1")
    external_sync._enforce_sync_rate_limit(req)
    external_sync._enforce_sync_rate_limit(req)
