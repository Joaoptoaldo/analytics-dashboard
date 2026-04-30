from backend.data import _build_seed_data
from backend.db import SessionLocal
from backend.models.product import Product

def seed_database():
    db = SessionLocal()
    try:
        seed_rows = _build_seed_data()
        for row in seed_rows:
            product = Product(
                client=row["client"],
                category=row["category"],
                revenue=row["revenue"],
                status=row["status"],
                region=row["region"],
                date=row["date"],
            )
            db.add(product)
        db.commit()
    finally:
        db.close()
