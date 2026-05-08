import logging
import os
import time
from pathlib import Path
from typing import Any

from sqlalchemy import event
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError
from urllib.parse import urlparse

# IMPORTANTE: Não usar fallback silencioso para DATABASE_URL
# Importar config validado (vai falhar se DATABASE_URL inválido)
from backend.config import DATABASE_URL, IS_DEVELOPMENT

# DATABASE_URL já foi validado em backend/config.py
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL não pode ser None. "
        "Verifique backend/config.py para validação de variáveis de ambiente."
    )


def _normalize_sqlite_url(database_url: str) -> str:
    """Resolve URLs SQLite relativas para um caminho absoluto baseado na raiz do repositório."""
    if not database_url.startswith("sqlite"):
        return database_url
    if database_url.startswith("sqlite:///:memory:"):
        return database_url

    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return database_url

    raw_path = database_url[len(prefix):]
    if raw_path.startswith("/") and not raw_path.startswith("//"):
        # já absoluto
        return database_url

    root_dir = Path(__file__).resolve().parents[1]
    absolute_path = (root_dir / raw_path.lstrip("./\\")).resolve()
    normalized = f"sqlite:///{absolute_path.as_posix()}"
    logging.info("[DB] Normalized sqlite path to %s", absolute_path)
    return normalized


# Configuração do engine para PostgreSQL (produção) ou SQLite (desenvolvimento validado)
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(_normalize_sqlite_url(DATABASE_URL), connect_args={"check_same_thread": False})
else:
    db_connect_timeout = int(os.getenv("DB_CONNECT_TIMEOUT_SECONDS", "5"))
    db_statement_timeout_ms = int(os.getenv("DB_STATEMENT_TIMEOUT_MS", "5000"))
    db_pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
    db_max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    db_pool_timeout = int(os.getenv("DB_POOL_TIMEOUT_SECONDS", "30"))
    db_pool_recycle = int(os.getenv("DB_POOL_RECYCLE_SECONDS", "1800"))

    logging.info(
        "[DB] Engine config: pool_size=%s max_overflow=%s pool_timeout=%ss pool_recycle=%ss connect_timeout=%ss statement_timeout=%sms",
        db_pool_size,
        db_max_overflow,
        db_pool_timeout,
        db_pool_recycle,
        db_connect_timeout,
        db_statement_timeout_ms,
    )

    parsed = urlparse(DATABASE_URL)
    host = (parsed.hostname or "").lower()
    is_neon_host = "neon.tech" in host or "neon" in host
    connect_args = {"connect_timeout": db_connect_timeout}

    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_size=db_pool_size,
        max_overflow=db_max_overflow,
        pool_timeout=db_pool_timeout,
        pool_recycle=db_pool_recycle,
    )

    if db_statement_timeout_ms > 0:

        @event.listens_for(engine, "connect")
        def _set_statement_timeout(dbapi_connection, _connection_record) -> None:
            try:
                with dbapi_connection.cursor() as cursor:
                    cursor.execute("SET statement_timeout = %s", (db_statement_timeout_ms,))
            except Exception:
                if is_neon_host:
                    logging.debug("[DB] Neon detected; skipping post-connect statement_timeout setup.", exc_info=False)
                    return
                raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def _db_host() -> str:
    return getattr(getattr(engine, "url", None), "host", None) or "unknown"


def check_database_readiness(
    max_attempts: int = 3,
    retry_delay_seconds: float = 0.25,
    slow_threshold_ms: float = 300.0,
) -> dict[str, Any]:
    started_at = time.perf_counter()
    db_host = _db_host()
    last_error_name: str | None = None

    for attempt in range(1, max_attempts + 1):
        attempt_started_at = time.perf_counter()
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                has_products_table = conn.dialect.has_table(conn, "products")

            attempt_latency_ms = round((time.perf_counter() - attempt_started_at) * 1000, 2)

            if not has_products_table:
                logging.error(
                    "[DB] Readiness schema check failed (host=%s attempt=%s/%s): missing table 'products'",
                    db_host,
                    attempt,
                    max_attempts,
                    exc_info=False,
                )
                return {
                    "ready": False,
                    "status": "not_ready",
                    "reason": "schema_missing",
                    "database": "ok",
                    "schema": "failed",
                    "latency_ms": attempt_latency_ms,
                    "db_host": db_host,
                    "error_name": None,
                }

            if attempt_latency_ms > slow_threshold_ms:
                last_error_name = "db_slow"
                logging.warning(
                    "[DB] Readiness slow (host=%s attempt=%s/%s latency_ms=%s threshold_ms=%s)",
                    db_host,
                    attempt,
                    max_attempts,
                    attempt_latency_ms,
                    slow_threshold_ms,
                )
                if attempt < max_attempts:
                    time.sleep(retry_delay_seconds)
                    continue

                return {
                    "ready": False,
                    "status": "not_ready",
                    "reason": "db_slow",
                    "database": "ok",
                    "schema": "ok",
                    "latency_ms": attempt_latency_ms,
                    "db_host": db_host,
                    "error_name": last_error_name,
                }

            return {
                "ready": True,
                "status": "ready",
                "reason": "ok",
                "database": "ok",
                "schema": "ok",
                "latency_ms": attempt_latency_ms,
                "db_host": db_host,
                "error_name": None,
            }

        except SQLAlchemyTimeoutError as exc:
            last_error_name = exc.__class__.__name__
            attempt_latency_ms = round((time.perf_counter() - attempt_started_at) * 1000, 2)
            logging.error(
                "[DB] Readiness acquire timed out (host=%s attempt=%s/%s latency_ms=%s): %s",
                db_host,
                attempt,
                max_attempts,
                attempt_latency_ms,
                last_error_name,
                exc_info=False,
            )
        except Exception as exc:
            last_error_name = exc.__class__.__name__
            attempt_latency_ms = round((time.perf_counter() - attempt_started_at) * 1000, 2)
            logging.error(
                "[DB] Readiness attempt failed (host=%s attempt=%s/%s latency_ms=%s): %s",
                db_host,
                attempt,
                max_attempts,
                attempt_latency_ms,
                last_error_name,
                exc_info=False,
            )

        if attempt < max_attempts:
            time.sleep(retry_delay_seconds)

    total_latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
    return {
        "ready": False,
        "status": "not_ready",
        "reason": "db_error",
        "database": "failed",
        "schema": "failed",
        "latency_ms": total_latency_ms,
        "db_host": db_host,
        "error_name": last_error_name,
    }


def ping_database_with_retry(max_attempts: int = 3, retry_delay_seconds: float = 0.25) -> tuple[bool, str | None]:
    result = check_database_readiness(max_attempts=max_attempts, retry_delay_seconds=retry_delay_seconds, slow_threshold_ms=float("inf"))
    return bool(result["ready"]), result["error_name"]



def init_db():
    try:
        from backend.models.product import Product
        from backend.models.sync_state import SyncState
    except Exception:
        pass

    if IS_DEVELOPMENT:
        Base.metadata.create_all(bind=engine)
        logging.info(
            "[DB] Ambiente de desenvolvimento detectado. Para popular o banco com seed, execute manualmente: backend/seeds/seed_data.py"
        )
