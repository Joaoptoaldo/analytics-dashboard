#!/usr/bin/env python
"""Validate frontend against backend API endpoints."""

import requests
import json

base = 'http://127.0.0.1:8000/api'

endpoints = {
    'overview': 'overview?period=all&category=all&status=all&search=',
    'sales/monthly': 'sales/monthly',
    'distribution/category': 'distribution/category',
    'top/products': 'top/products?limit=10',
}

print("=== API VALIDATION ===\n")

for name, path in endpoints.items():
    try:
        r = requests.get(f'{base}/{path}', timeout=5)
        data = r.json()
        
        if name == 'overview':
            print(f"[OVERVIEW]")
            print(f"  Revenue: USD {data['total_revenue']:.2f}")
            print(f"  Orders: {data['total_orders']}")
            print(f"  Customers: {data['total_customers']}")
            print(f"  Conversion: {data['conversion_rate']:.2f}%")
            print(f"  Revenue Change: {data['revenue_change']}")
            print(f"  Orders Change: {data['orders_change']}")
            
        elif name == 'sales/monthly':
            print(f"\n[SALES/MONTHLY]")
            print(f"  State: {data['state']}")
            print(f"  Months: {len(data['data'])}")
            for item in data['data'][:3]:
                print(f"    {item['month']}: orders={item['orders']}, revenue=USD {item['revenue']:.2f}")
            print(f"    ...")
                
        elif name == 'distribution/category':
            print(f"\n[DISTRIBUTION/CATEGORY]")
            print(f"  State: {data['state']}")
            print(f"  Categories: {len(data['data'])}")
            total = sum(c.get('count', c.get('orders', 0)) for c in data['data'])
            for i, cat in enumerate(data['data'][:5], 1):
                cnt = cat.get('count', cat.get('orders', 0))
                pct = (cnt / total * 100) if total else 0
                print(f"    {i}. {cat['category']}: {cnt} ({pct:.1f}%)")
                
        elif name == 'top/products':
            print(f"\n[TOP/PRODUCTS]")
            print(f"  State: {data['state']}")
            print(f"  Top items: {len(data['data'])}")
            for i, prod in enumerate(data['data'][:5], 1):
                print(f"    {i}. {prod['product_name'][:30]:30s}: USD {prod['revenue']:.2f}")
                
    except Exception as e:
        print(f"\n[{name}] ERROR: {e}")

print("\n=== COMPARISON WITH DB ===")
print("DB: Revenue=USD 35,577.50, Orders=62, Customers=36, Conversion=16.13%")
print("Expected: API should match exactly (period=all filters)")
