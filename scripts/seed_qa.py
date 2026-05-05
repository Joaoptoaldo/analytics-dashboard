#!/usr/bin/env python
"""Quick seeder for QA tests"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ['ENV'] = 'development'
os.environ['DATABASE_URL'] = f"sqlite:///{(BASE_DIR / 'backend_qa.db').as_posix()}"
os.environ['ALLOW_SEED'] = 'true'

from datetime import datetime, timedelta
from backend.db import SessionLocal
from backend.models.product import Product

def seed_products():
    db = SessionLocal()
    
    # Check if already seeded
    count = db.query(Product).count()
    if count > 0:
        print(f"Database already has {count} products. Skipping seed.")
        db.close()
        return
    
    products = []
    categories = ['Electronics', 'Clothing', 'Books', 'Home', 'Sports']
    statuses = ['active', 'inactive', 'pending']
    clients = ['Client A', 'Client B', 'Client C', 'Client D', 'Client E']
    
    base_date = datetime.now().date()
    
    # Create 50 sample products
    for i in range(50):
        product = Product(
            client=clients[i % len(clients)],
            category=categories[i % len(categories)],
            revenue=(i * 100 + 50) * (1 if i % 2 == 0 else 1.5),
            status=statuses[i % len(statuses)],
            date=base_date - timedelta(days=i % 180),
            is_synthetic=False  # Mark as real data for filtering
        )
        products.append(product)
    
    db.add_all(products)
    db.commit()
    
    print(f"✅ Seeded {len(products)} products successfully!")
    db.close()

if __name__ == "__main__":
    seed_products()
