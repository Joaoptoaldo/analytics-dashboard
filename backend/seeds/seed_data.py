import os

from backend.db import SessionLocal
from backend.models.product import Product
from backend.data import _build_seed_data
from datetime import datetime


def seed_database():
    """_summary_: Popula o banco com dados de seed em ambiente de desenvolvimento.

    Raises:
        RuntimeError: _description_: Lancada quando `ENV!=development` ou `ALLOW_SEED!=true`.
    """
    ENV = os.getenv("ENV", "production")
    ALLOW_SEED = os.getenv("ALLOW_SEED", "false").lower() == "true"
    if ENV != "development" or not ALLOW_SEED:
        raise RuntimeError("Seed execution is forbidden outside development with ALLOW_SEED=true")
    db = SessionLocal()
    try:
        seed_rows = _build_seed_data()
        for i, row in enumerate(seed_rows):
            # Ensure `date` is a Python date object for SQLite Date column
            d = row.get("date")
            if isinstance(d, str):
                try:
                    d = datetime.strptime(d[:10], "%Y-%m-%d").date()
                except Exception:
                    d = None

            # Mark first 50 records (older) as synthetic (test data)
            # Mark last 50 records (recent) as real (for demo/testing)
            is_synthetic = i < 50

            product = Product(
                client=row["client"],
                category=row["category"],
                revenue=row["revenue"],
                status=row["status"],
                date=d,
                is_synthetic=is_synthetic,
            )
            db.add(product)
        db.commit()
    finally:
        db.close()
