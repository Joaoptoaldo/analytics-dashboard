from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

from sqlalchemy import inspect, text

from backend.config import DATABASE_URL
from backend.db import engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class BootstrapError(RuntimeError):
    pass


def _require_database_url() -> str:
    if not DATABASE_URL or not DATABASE_URL.strip():
        raise BootstrapError("DATABASE_URL ausente")
    return DATABASE_URL.strip()


def _require_sslmode(database_url: str) -> None:
    parsed = urlparse(database_url)
    if parsed.scheme.startswith("sqlite"):
        return

    params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    sslmode = params.get("sslmode", "").strip().lower()
    if not sslmode:
        raise BootstrapError("DATABASE_URL sem sslmode")
    if sslmode not in {"require", "verify-full"}:
        raise BootstrapError(f"sslmode inválido para bootstrap: {sslmode}")


def _test_connection() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def _run_alembic_upgrade() -> None:
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(PROJECT_ROOT))
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(PROJECT_ROOT),
        env=env,
        check=True,
    )


def _validate_schema() -> list[str]:
    required_tables = {"products", "sync_state"}
    inspector = inspect(engine)
    missing = sorted(required_tables.difference(inspector.get_table_names()))
    if missing:
        raise BootstrapError(f"schema incompleto: {missing}")
    return sorted(required_tables)


def _schema_is_present() -> bool:
    required_tables = {"products", "sync_state"}
    inspector = inspect(engine)
    return required_tables.issubset(set(inspector.get_table_names()))


def _run_alembic_stamp() -> None:
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(PROJECT_ROOT))
    subprocess.run(
        [sys.executable, "-m", "alembic", "stamp", "head"],
        cwd=str(PROJECT_ROOT),
        env=env,
        check=True,
    )


def _ensure_migrations_applied() -> None:
    try:
        _run_alembic_upgrade()
        return
    except subprocess.CalledProcessError as exc:
        if not _schema_is_present():
            raise BootstrapError("falha ao aplicar migrations") from exc

        _run_alembic_stamp()
        _run_alembic_upgrade()


def _default_command() -> list[str]:
    port = os.getenv("PORT", "8080")
    web_concurrency = os.getenv("WEB_CONCURRENCY", "2")
    gunicorn_timeout = os.getenv("GUNICORN_TIMEOUT", "60")
    gunicorn_graceful_timeout = os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30")
    gunicorn_keepalive = os.getenv("GUNICORN_KEEPALIVE", "5")
    if os.name == "nt":
        return [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            port,
            "--log-level",
            "info",
        ]

    return [
        sys.executable,
        "-m",
        "gunicorn",
        "-k",
        "uvicorn.workers.UvicornWorker",
        "-w",
        web_concurrency,
        "-b",
        f"0.0.0.0:{port}",
        "backend.main:app",
        "--log-level",
        "info",
        "--access-logfile",
        "-",
        "--error-logfile",
        "-",
        "--capture-output",
        "--timeout",
        gunicorn_timeout,
        "--graceful-timeout",
        gunicorn_graceful_timeout,
        "--keep-alive",
        gunicorn_keepalive,
    ]


def run_bootstrap(preflight_only: bool = False, command: list[str] | None = None) -> int:
    database_url = _require_database_url()
    _require_sslmode(database_url)
    _test_connection()
    _ensure_migrations_applied()
    _validate_schema()

    if preflight_only:
        return 0

    final_command = command or _default_command()
    os.execvp(final_command[0], final_command)
    return 0


def main() -> int:
    args = sys.argv[1:]
    preflight_only = False
    command: list[str] | None = None

    if "--preflight-only" in args:
        preflight_only = True
        args = [arg for arg in args if arg != "--preflight-only"]

    if "--" in args:
        separator = args.index("--")
        command = args[separator + 1 :]

    return run_bootstrap(preflight_only=preflight_only, command=command)


if __name__ == "__main__":
    raise SystemExit(main())