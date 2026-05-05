import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import inspect, text

from backend.config import GLOBAL_CONFIG
from backend.db import engine, ping_database_with_retry


def main() -> int:
    print("[STARTUP] config loaded", GLOBAL_CONFIG.get("env"))

    ok, error_name = ping_database_with_retry(max_attempts=3, retry_delay_seconds=0.25)
    if not ok:
        print(f"[DB] ping failed: {error_name}")
        return 1

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            has_products = inspect(conn).has_table("products")
    except Exception as exc:
        import traceback
        print(f"[DB] validation query failed: {exc.__class__.__name__}")
        traceback.print_exc()
        return 1

    if not has_products:
        print("[DB] schema invalid: missing table 'products'")
        return 1

    print("[DB] runtime validation OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
