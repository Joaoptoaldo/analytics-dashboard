from backend.db import SessionLocal
from backend.models.product import Product
from sqlalchemy import func

s = SessionLocal()
try:
    total = s.query(func.count(Product.id)).scalar()
    min_date = s.query(func.min(Product.date)).scalar()
    max_date = s.query(func.max(Product.date)).scalar()
    sample = s.query(Product).order_by(Product.date.desc()).limit(10).all()
    print('total=', total)
    print('min_date=', min_date)
    print('max_date=', max_date)
    for p in sample:
        print(p.id, p.external_id, p.client, p.date)
finally:
    s.close()
