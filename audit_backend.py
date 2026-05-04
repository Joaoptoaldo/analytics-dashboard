#!/usr/bin/env python
"""Audit backend data for dashboard validation."""

from backend.db import SessionLocal
from backend.models.product import Product
from sqlalchemy import func

db = SessionLocal()
try:
    # 1. KPI totals
    total_orders = db.query(func.count(Product.id)).scalar() or 0
    total_revenue = db.query(func.sum(Product.revenue)).scalar() or 0.0
    total_customers = db.query(func.count(func.distinct(Product.client))).scalar() or 0
    completed = db.query(func.count(Product.id)).filter(Product.status == 'Completed').scalar() or 0
    conversion = (completed / total_orders * 100) if total_orders else 0
    
    print("=== KPI TOTALS (from DB) ===")
    print(f"Total Orders: {total_orders}")
    print(f"Total Revenue: USD {total_revenue:.2f}")
    print(f"Total Customers: {total_customers}")
    print(f"Completed Orders: {completed}")
    print(f"Conversion Rate: {conversion:.2f}%")
    
    # 2. Category distribution
    print("\n=== DISTRIBUTION BY CATEGORY (top 8) ===")
    cats = db.query(Product.category, func.count(Product.id).label('cnt')).group_by(Product.category).order_by(func.count(Product.id).desc()).all()
    total_cat = sum(c[1] for c in cats)
    for c in cats[:8]:
        pct = (c[1] / total_cat * 100) if total_cat else 0
        print(f"{c[0]:20s}: {c[1]:3d} ({pct:5.1f}%)")
    
    # 3. Top 10 by revenue
    print("\n=== TOP 10 PRODUCTS BY REVENUE ===")
    tops = db.query(Product.client, Product.revenue, Product.date).order_by(Product.revenue.desc()).limit(10).all()
    for i, t in enumerate(tops, 1):
        print(f"{i:2d}. {str(t[0])[:35]:35s}: USD {t[1]:8.2f} @ {t[2]}")
    
    # 4. Monthly aggregation (all data)
    print("\n=== MONTHLY AGGREGATION ===")
    months = db.query(func.strftime('%Y-%m', Product.date).label('m'), 
                      func.count(Product.id).label('cnt'),
                      func.sum(Product.revenue).label('rev')).group_by('m').order_by('m').all()
    for m in months:
        print(f"{m[0]}: orders={m[1]:3d}, revenue=USD {m[2]:10.2f}")
    
    # 5. Data quality
    print("\n=== DATA QUALITY ===")
    nulldates = db.query(func.count(Product.id)).filter(Product.date.is_(None)).scalar() or 0
    print(f"Records with null date: {nulldates}")
    
    # 6. Date range
    print("\n=== DATE RANGE ===")
    mindate = db.query(func.min(Product.date)).scalar()
    maxdate = db.query(func.max(Product.date)).scalar()
    print(f"Min date: {mindate}")
    print(f"Max date: {maxdate}")
    if maxdate and mindate:
        print(f"Span: {(maxdate - mindate).days} days")
    
finally:
    db.close()
