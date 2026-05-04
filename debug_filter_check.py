#!/usr/bin/env python3
"""Debug: Verificar se filtro está aplicado na função"""
import os
os.environ["ENV"] = "development"
os.environ["ALLOW_SEED"] = "true"

from backend.db import SessionLocal
from backend.models.product import Product
from sqlalchemy import func

db = SessionLocal()
try:
    # Teste 1: Sem filtro (todos)
    all_with_date = db.query(func.count(Product.id)).filter(Product.date.isnot(None)).scalar() or 0
    print(f"All records with date.isnot(None): {all_with_date}")
    
    # Teste 2: Apenas is_synthetic=False
    real_with_date = db.query(func.count(Product.id)).filter(Product.is_synthetic == False, Product.date.isnot(None)).scalar() or 0
    print(f"Records with is_synthetic=False AND date.isnot(None): {real_with_date}")
    
    # Teste 3: Apenas is_synthetic=True
    synthetic_with_date = db.query(func.count(Product.id)).filter(Product.is_synthetic == True, Product.date.isnot(None)).scalar() or 0
    print(f"Records with is_synthetic=True AND date.isnot(None): {synthetic_with_date}")
    
    # Teste 4: Via query like in get_sales_monthly
    base_query = db.query(Product).filter(Product.date.isnot(None), Product.is_synthetic == False)
    monthly_count = base_query.with_entities(func.count(Product.id)).scalar() or 0
    print(f"Via base_query (like get_sales_monthly): {monthly_count}")
    
    print(f"\nSum: {real_with_date} = {synthetic_with_date} + {real_with_date}")
finally:
    db.close()
