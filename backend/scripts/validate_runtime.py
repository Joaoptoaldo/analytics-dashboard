import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import inspect, text

from backend.config import GLOBAL_CONFIG
from backend.db import check_database_readiness


def main() -> int:
    """_summary_: script de validação do runtime, que verifica a conectividade e prontidão do banco de dados antes de iniciar a aplicação, para garantir que o ambiente esteja configurado corretamente e evitar falhas em tempo de execução devido a problemas de conexão com o banco

    Returns:
        int: _description_: retorna 0 se a validação for bem-sucedida (banco pronto), ou 1 se a validação falhar (banco não pronto ou erro de conexão)
    """
    print("[STARTUP] config loaded", GLOBAL_CONFIG.get("env"))

    result = check_database_readiness(max_attempts=3, retry_delay_seconds=0.25, slow_threshold_ms=300.0)

    if not result["ready"]:
        print(
            f"[DB] validation failed host={result.get('db_host', 'unknown')} "
            f"reason={result.get('reason', 'db_error')} error={result.get('error_name', 'unknown')} "
            f"latency_ms={result.get('latency_ms', 0)}"
        )
        return 1

    print("[DB] runtime validation OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
