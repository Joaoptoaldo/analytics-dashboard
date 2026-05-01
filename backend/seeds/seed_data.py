import os

from backend.db import SessionLocal
from backend.models.product import Product
from backend.data import _build_seed_data


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
        for row in seed_rows:
            product = Product(
                client=row["client"],
                category=row["category"],
                revenue=row["revenue"],
                status=row["status"],
                date=row["date"],
            )
            db.add(product)
        db.commit()
    finally:
        db.close()
