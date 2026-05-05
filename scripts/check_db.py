#!/usr/bin/env python
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ['ENV'] = 'development'
os.environ['DATABASE_URL'] = f"sqlite:///{(BASE_DIR / 'backend_qa.db').as_posix()}"

from backend.db import SessionLocal
from backend.models.product import Product

db = SessionLocal()
count = db.query(Product).count()
print(f"Total products in DB: {count}")

# Get first few
first = db.query(Product).limit(5).all()
for p in first:
    print(f"  - {p.id}: {p.client} | {p.category} | {p.revenue} | {p.date}")

db.close()
