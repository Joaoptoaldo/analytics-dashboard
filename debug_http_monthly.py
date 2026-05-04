#!/usr/bin/env python3
"""Debug: Chamar endpoint HTTP de sales/monthly"""
import requests

BASE_URL = "http://127.0.0.1:8000/api"

r = requests.get(f"{BASE_URL}/sales/monthly", timeout=5)
print(f"Status: {r.status_code}")
data = r.json()
print(f"State: {data['state']}")
if data['state'] == 'valid':
    months = data['data']
    total = sum(m['orders'] for m in months)
    revenue = sum(m['revenue'] for m in months) if months else 0
    print(f"Months: {len(months)}")
    print(f"Total orders: {total}")
    print(f"Total revenue: USD {revenue:.2f}")
    print("\nMonthly breakdown:")
    for m in months:
        print(f"  {m['month']}: {m['orders']} orders, USD {m['revenue']:.2f}")
