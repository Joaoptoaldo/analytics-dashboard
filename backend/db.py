import logging
import os
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text
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

# Configuração do engine para PostgreSQL (produção) ou SQLite (desenvolvimento validado)
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
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
    connect_args = {"connect_timeout": db_connect_timeout}
    if "neon" not in host:
        connect_args["options"] = f"-c statement_timeout={db_statement_timeout_ms}"

    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_size=db_pool_size,
        max_overflow=db_max_overflow,
        pool_timeout=db_pool_timeout,
        pool_recycle=db_pool_recycle,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ping_database_with_retry(max_attempts: int = 3, retry_delay_seconds: float = 0.25) -> tuple[bool, str | None]:
    last_error_name = None
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, None
        except Exception as exc:
            last_error_name = exc.__class__.__name__
            logging.error(
                "[DB] Ping failed (attempt %s/%s): %s",
                attempt,
                max_attempts,
                last_error_name,
                exc_info=False,
            )
            if attempt < max_attempts:
                time.sleep(retry_delay_seconds)

    return False, last_error_name



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
