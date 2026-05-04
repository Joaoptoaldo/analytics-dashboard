from datetime import datetime, timedelta
import random

from backend.db import SessionLocal
from backend.models.product import Product


def backfill(days: int = 180, records: int = 180) -> int:
    db = SessionLocal()
    try:
        random.seed(2026)
        end = datetime.now().date()
        start = end - timedelta(days=days)
        days_range = (end - start).days or 1
        inserted = 0
        for i in range(records):
            d = start + timedelta(days=(i * days_range) // records)
            p = Product(
                client=f"Backfill {i}",
                category="backfill",
                revenue=round(50 + random.random() * 500, 2),
                status="Completed",
                date=d,
            )
            db.add(p)
            inserted += 1
        db.commit()
        return inserted
    finally:
        db.close()


if __name__ == "__main__":
    n = backfill(days=180, records=180)
    print(f"Inserted {n} backfill records over last 180 days")
