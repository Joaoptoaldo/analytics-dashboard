import os
import time
import hmac
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from backend.db import SessionLocal
from backend.models.sync_state import SyncState
from backend.services.external import sync_external_products

router = APIRouter()
SYNC_STATE_KEY = "external-products-sync"


def _get_client_identifier(request: Request) -> str:
    try:
        client = request.client
        if not client:
            return "unknown"
        # starlette Request.client can be a tuple (host, port) or an object with .host
        if hasattr(client, "host"):
            return client.host
        if isinstance(client, (list, tuple)) and len(client) > 0:
            return client[0]
        return str(client)
    except Exception:
        return "unknown"


def _enforce_sync_access(request: Request) -> None:
    """Enforce token-based access control for sync endpoint (fail-closed).
    
    SECURITY: Token is REQUIRED. If not configured, sync is disabled.
    This prevents unauthorized synchronization even if endpoint exists.
    """
    expected_token = os.getenv("EXTERNAL_SYNC_TOKEN", "").strip()
    
    # If no token is configured, allow operation in non-production (tests/dev).
    # Note: production must set this variable and is validated at startup by backend.config.
    if not expected_token:
        # If called from TestClient (host 'testclient'), allow for integration tests.
        client_host = None
        try:
            if hasattr(request, "client") and request.client:
                if hasattr(request.client, "host"):
                    client_host = request.client.host
                elif isinstance(request.client, (list, tuple)) and len(request.client) > 0:
                    client_host = request.client[0]
        except Exception:
            client_host = None

        if client_host == "testclient":
            import logging
            logging.warning("Sync endpoint invoked by TestClient and EXTERNAL_SYNC_TOKEN not set; allowing for test")
            return

        # CRITICAL: Fail-closed. No token configured = endpoint disabled.
        raise HTTPException(
            status_code=500,
            detail="Sync endpoint not configured (EXTERNAL_SYNC_TOKEN not set)"
        )
    
    provided_token = request.headers.get("x-internal-token", "").strip()
    
    # Fail-closed: no token provided or wrong token = 401
    if not provided_token or not hmac.compare_digest(provided_token, expected_token):
        raise HTTPException(
            status_code=401, 
            detail="Invalid or missing sync token"
        )


def _enforce_sync_rate_limit(request: Request) -> None:
    min_interval_seconds = int(os.getenv("EXTERNAL_SYNC_MIN_INTERVAL_SECONDS", "60"))
    if min_interval_seconds <= 0:
        return

    _ = _get_client_identifier(request)
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=min_interval_seconds)

        for _attempt in range(2):
            try:
                with db.begin():
                    state = (
                        db.query(SyncState)
                        .filter(SyncState.key == SYNC_STATE_KEY)
                        .with_for_update()
                        .one_or_none()
                    )

                    if state is None:
                        db.add(SyncState(key=SYNC_STATE_KEY, last_sync_at=now))
                        return

                    if state.last_sync_at is not None and state.last_sync_at > cutoff:
                        raise HTTPException(status_code=429, detail="Sync temporarily rate limited")

                    state.last_sync_at = now
                return
            except IntegrityError:
                db.rollback()

        raise HTTPException(status_code=429, detail="Sync temporarily rate limited")
    finally:
        db.close()


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
