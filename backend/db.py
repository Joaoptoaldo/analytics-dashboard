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
    """_summary_: normaliza a URL do SQLite para garantir que o caminho do arquivo seja absoluto, evitando problemas de caminho relativo que podem ocorrer dependendo do diretório de trabalho ao iniciar a aplicação, especialmente em ambientes de desenvolvimento. Se a URL já for absoluta ou for um banco em memória, ela é retornada sem alterações. Caso contrário, o caminho é convertido para absoluto com base no diretório raiz do projeto

    Args:
        database_url (str): _description_: a URL de conexão do banco de dados SQLite, que pode ser relativa ou absoluta, e será normalizada para garantir que o caminho do arquivo seja absoluto para evitar problemas de conexão dependendo do diretório de trabalho ao iniciar a aplicação

    Returns:
        str: _description_: a URL de conexão do banco de dados SQLite normalizada, garantindo que o caminho do arquivo seja absoluto para evitar problemas de conexão, especialmente em ambientes de desenvolvimento onde o diretório de trabalho pode variar
    """
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
    """_summary_: extrai o host do banco de dados a partir da URL de conexão para fins de monitoramento e logging, retornando "unknown" se o host não puder ser determinado, para fornecer informações sobre o banco de dados conectado sem expor detalhes sensíveis da URL completa

    Returns:
        str: _description_: o host do banco de dados, ou "unknown" se não puder ser determinado
    """
    return getattr(getattr(engine, "url", None), "host", None) or "unknown"


def check_database_readiness(
    max_attempts: int = 3,
    retry_delay_seconds: float = 0.25,
    slow_threshold_ms: float = 300.0,
) -> dict[str, Any]:
    """_summary_: verifica a prontidão do banco de dados realizando tentativas de conexão e validação de esquema, para garantir que o banco de dados esteja acessível e configurado corretamente antes de iniciar a aplicação, retornando um dicionário com o status da prontidão, motivo, latência e outras informações relevantes para monitoramento e diagnóstico

    Args:
        max_attempts (int, optional): _description_. Defaults to 3.
        retry_delay_seconds (float, optional): _description_. Defaults to 0.25.
        slow_threshold_ms (float, optional): _description_. Defaults to 300.0.

    Returns:
        dict[str, Any]: _description_: um dicionário contendo informações sobre a prontidão do banco de dados, incluindo:
            - `ready` (bool): indica se o banco de dados está pronto para uso (True) ou não (False)
            - `status` (str): um status geral da prontidão, como "ready" ou "not_ready"
            - `reason` (str): um motivo específico para o status, como "ok", "db_error", "schema_missing", ou "db_slow"
            - `database` (str): o status da conectividade com o banco de dados, como "ok" ou "failed"
            - `schema` (str): o status da validação do esquema, como "ok" ou "failed"
            - `latency_ms` (float): a latência em milissegundos para a tentativa de conexão e validação, para monitoramento de desempenho
            - `db_host` (str): o host do banco de dados conectado, para fins de monitoramento e diagnóstico, sem expor detalhes sensíveis da URL completa
            - `error_name` (str | None): o nome da última exceção de erro ocorrida durante as tentativas, ou None se não houver erros, para fins de diagnóstico e monitoramento de falhas do banco de dados 
    """
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
    """_summary_: realiza uma tentativa de ping no banco de dados com múltiplas tentativas e atraso entre elas, para verificar a conectividade com o banco de dados de forma resiliente, retornando um tuple indicando se o ping foi bem-sucedido e o nome do erro caso tenha falhado após todas as tentativas, para fornecer uma verificação rápida da disponibilidade do banco de dados sem realizar validação de esquema completa

    Args:
        max_attempts (int, optional): _description_. Defaults to 3.
        retry_delay_seconds (float, optional): _description_. Defaults to 0.25.

    Returns:
        tuple[bool, str | None]: _description_: um tuple onde o primeiro elemento é um booleano indicando se o ping foi bem-sucedido (True) ou não (False), e o segundo elemento é o nome do erro ocorrido durante as tentativas de ping, ou None se o ping foi bem-sucedido, para fins de diagnóstico e monitoramento da disponibilidade do banco de dados
    """
    result = check_database_readiness(max_attempts=max_attempts, retry_delay_seconds=retry_delay_seconds, slow_threshold_ms=float("inf"))
    return bool(result["ready"]), result["error_name"]



def init_db():
    """_summary_: inicializa o banco de dados criando as tabelas necessárias com base nos modelos definidos, para garantir que o esquema do banco de dados esteja configurado corretamente antes de iniciar a aplicação, especialmente em ambientes de desenvolvimento onde a criação automática de tabelas é conveniente, enquanto em produção espera-se que o banco já esteja migrado e pronto para uso
    """
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
