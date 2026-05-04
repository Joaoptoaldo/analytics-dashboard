#!/usr/bin/env python3
"""Debug: Verificar quantidade de registros no banco"""
import os
os.environ["ENV"] = "development"
os.environ["ALLOW_SEED"] = "true"

from backend.db import SessionLocal
from backend.models.product import Product
from sqlalchemy import func

db = SessionLocal()
try:
    total = db.query(func.count(Product.id)).scalar() or 0
    synthetic = db.query(func.count(Product.id)).filter(Product.is_synthetic == True).scalar() or 0
    real = db.query(func.count(Product.id)).filter(Product.is_synthetic == False).scalar() or 0
    
    print(f"Total records: {total}")
    print(f"Synthetic (is_synthetic=True): {synthetic}")
    print(f"Real (is_synthetic=False): {real}")
    print(f"\nDates in real data:")
    dates = db.query(Product.date).filter(Product.is_synthetic == False).distinct().order_by(Product.date).all()
    print(f"  Count: {len(dates)}")
    print(f"  Min: {dates[0][0] if dates else 'N/A'}")
    print(f"  Max: {dates[-1][0] if dates else 'N/A'}")
finally:
    db.close()
