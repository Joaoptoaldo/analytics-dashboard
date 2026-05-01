import os
import time

from fastapi import APIRouter, HTTPException, Request

from backend.services.external import sync_external_products

router = APIRouter()
_last_sync_request_at: dict[str, float] = {}


def _get_client_identifier(request: Request) -> str:
    if request.client and request.client.host:
                return request.client.host
    return "unknown"


def _enforce_sync_access(request: Request) -> None:
    expected_token = os.getenv("EXTERNAL_SYNC_TOKEN", "").strip()
    if expected_token:
        provided_token = request.headers.get("x-internal-token", "").strip()
        if provided_token != expected_token:
            raise HTTPException(status_code=401, detail="Unauthorized")


def _enforce_sync_rate_limit(request: Request) -> None:
    min_interval_seconds = int(os.getenv("EXTERNAL_SYNC_MIN_INTERVAL_SECONDS", "60"))
    if min_interval_seconds <= 0:
        return

    client_key = _get_client_identifier(request)
    now = time.monotonic()
    last_request = _last_sync_request_at.get(client_key)
    if last_request is not None and now - last_request < min_interval_seconds:
        raise HTTPException(status_code=429, detail="Sync temporarily rate limited")
    _last_sync_request_at[client_key] = now


@router.post("/external-products/sync")
def post_sync_external_products(request: Request):
    """_summary_: Sincroniza os produtos da API externa com o banco local.

    Returns:
        _type_: _description_: Dicionário com chave `synced`, contendo o total de registros processados (inseridos ou atualizados).
    """
    _enforce_sync_access(request)
    _enforce_sync_rate_limit(request)
    count = sync_external_products()
    return {"synced": count}
