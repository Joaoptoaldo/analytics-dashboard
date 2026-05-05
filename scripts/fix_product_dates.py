import sys
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.db import SessionLocal
from backend.models.product import Product

THRESHOLD_YEARS = 2

def fix_dates():
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        min_allowed = today - timedelta(days=365 * THRESHOLD_YEARS)
        products = db.query(Product).all()
        updated = 0
        for p in products:
            bad = False
            if p.date is None:
                bad = True
            elif p.date > today:
                bad = True
            elif p.date < min_allowed:
                bad = True
            if bad:
                key = p.external_id if p.external_id else p.id
                try:
                    key_int = int(key)
                except Exception:
                    key_int = p.id
                new_date = today - timedelta(days=(key_int % 365))
                p.date = new_date
                updated += 1
        if updated:
            db.commit()
        print(f"Total products: {len(products)}; Updated dates: {updated}")
    finally:
        db.close()

if __name__ == '__main__':
    fix_dates()
