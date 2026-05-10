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
    """_summary_: verifica se DATABASE_URL está presente e não é vazia

    Raises:
        BootstrapError: _description_: se DATABASE_URL estiver ausente ou vazia

    Returns:
        str: _description_: a string de conexão do banco de dados, sem espaços em branco
    """
    if not DATABASE_URL or not DATABASE_URL.strip():
        raise BootstrapError("DATABASE_URL ausente")
    return DATABASE_URL.strip()


def _require_sslmode(database_url: str) -> None:
    """_summary_: verifica se a string de conexão do banco de dados contém um parâmetro sslmode válido

    Args:
        database_url (str): _description_: a string de conexão do banco de dados a ser verificada

    Raises:
        BootstrapError: _description_: se sslmode estiver ausente ou vazio
        BootstrapError: _description_: se sslmode tiver um valor inválido (não "require" ou "verify-full")
    """
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
    """_summary_: testa a conexão com o banco de dados executando uma consulta simples
    """
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def _run_alembic_upgrade() -> None:
    """_summary_: executa o comando "alembic upgrade head" para aplicar as migrations pendentes
    """
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(PROJECT_ROOT))
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(PROJECT_ROOT),
        env=env,
        check=True,
    )


def _validate_schema() -> list[str]:
    """_summary_: valida se as tabelas necessárias estão presentes no banco de dados

    Raises:
        BootstrapError: _description_: se alguma das tabelas necessárias estiver ausente

    Returns:
        list[str]: _description_: uma lista ordenada dos nomes das tabelas necessárias que estão presentes no banco de dados
    """
    required_tables = {"products", "sync_state"}
    inspector = inspect(engine)
    missing = sorted(required_tables.difference(inspector.get_table_names()))
    if missing:
        raise BootstrapError(f"schema incompleto: {missing}")
    return sorted(required_tables)


def _schema_is_present() -> bool:
    """_summary_: verifica se as tabelas necessárias estão presentes no banco de dados

    Returns:
        bool: _description_: True se todas as tabelas necessárias estiverem presentes, False caso contrário
    """
    required_tables = {"products", "sync_state"}
    inspector = inspect(engine)
    return required_tables.issubset(set(inspector.get_table_names()))


def _run_alembic_stamp() -> None:
    """_summary_: executa o comando "alembic stamp head" para marcar o banco de dados como atualizado para a versão mais recente das migrations, sem aplicar nenhuma migration
    """
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(PROJECT_ROOT))
    subprocess.run(
        [sys.executable, "-m", "alembic", "stamp", "head"],
        cwd=str(PROJECT_ROOT),
        env=env,
        check=True,
    )


def _ensure_migrations_applied() -> None:
    """_summary_: garante que as migrations estejam aplicadas, tentando aplicar as migrations normalmente e, se falhar, verificando se o schema está presente. Se o schema estiver presente, marca o banco de dados como atualizado para a versão mais recente das migrations e tenta aplicar as migrations novamente. Se o schema não estiver presente, levanta um erro de bootstrap

    Raises:
        BootstrapError: _description_: se as migrations falharem e o schema não estiver presente
    """
    try:
        _run_alembic_upgrade()
        return
    except subprocess.CalledProcessError as exc:
        if not _schema_is_present():
            raise BootstrapError("falha ao aplicar migrations") from exc

        _run_alembic_stamp()
        _run_alembic_upgrade()


def _default_command() -> list[str]:
    """_summary_: constrói o comando padrão para iniciar o servidor, usando gunicorn com uvicorn workers no Linux e uvicorn diretamente no Windows

    Returns:
        list[str]: _description_: uma lista de strings representando o comando e seus argumentos para iniciar o servidor
    """
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
    """_summary_: executa o processo de bootstrap, verificando a string de conexão do banco de dados, testando a conexão, garantindo que as migrations estejam aplicadas e validando o schema. Se preflight_only for True, apenas executa as verificações e retorna 0. Caso contrário, executa o comando fornecido ou o comando padrão para iniciar o servidor

    Args:
        preflight_only (bool, optional): _description_. Defaults to False.
        command (list[str] | None, optional): _description_. Defaults to None.

    Returns:
        int: _description_: o código de saída do processo, 0 se tudo correr bem, ou um código de erro se ocorrer um erro de bootstrap
    """
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
    """_summary_: main function para executar o processo de bootstrap, processando os argumentos da linha de comando para determinar se deve executar apenas as verificações pré-voo ou também iniciar o servidor com um comando personalizado

    Returns:
        int: _description_: o código de saída do processo, 0 se tudo correr bem, ou um código de erro se ocorrer um erro de bootstrap
    """
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