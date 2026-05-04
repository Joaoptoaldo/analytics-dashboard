import os
import time
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from backend.db import Base, SessionLocal, engine
from backend.models.sync_state import SyncState
from backend.services.external import sync_external_products

router = APIRouter()
SYNC_STATE_KEY = "external-products-sync"

Base.metadata.create_all(bind=engine)


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
    expected_token = os.getenv("EXTERNAL_SYNC_TOKEN", "").strip()
    if expected_token:
        provided_token = request.headers.get("x-internal-token", "").strip()
        if provided_token != expected_token:
            raise HTTPException(status_code=401, detail="Unauthorized")


def _enforce_sync_rate_limit(request: Request) -> None:
    min_interval_seconds = int(os.getenv("EXTERNAL_SYNC_MIN_INTERVAL_SECONDS", "60"))
    if min_interval_seconds <= 0:
        return

    _ = _get_client_identifier(request)
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=min_interval_seconds)

        state = db.get(SyncState, SYNC_STATE_KEY)
        if state is None:
            db.add(SyncState(key=SYNC_STATE_KEY, last_sync_at=now))
            try:
                db.commit()
                return
            except IntegrityError:
                db.rollback()

        updated_rows = (
            db.query(SyncState)
            .filter(
                SyncState.key == SYNC_STATE_KEY,
                or_(SyncState.last_sync_at.is_(None), SyncState.last_sync_at <= cutoff),
            )
            .update({SyncState.last_sync_at: now}, synchronize_session=False)
        )

        if updated_rows == 0:
            db.rollback()
            raise HTTPException(status_code=429, detail="Sync temporarily rate limited")

        db.commit()
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
