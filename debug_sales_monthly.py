#!/usr/bin/env python3
"""Debug: Chamar get_sales_monthly diretamente"""
import os
os.environ["ENV"] = "development"
os.environ["ALLOW_SEED"] = "true"

from backend.services.analytics import get_sales_monthly

result = get_sales_monthly(period="all", category="all", status="all", search="")
print(f"State: {result['state']}")
if result['state'] == 'valid':
    total = sum(m['orders'] for m in result['data'])
    revenue = sum(m['revenue'] for m in result['data']) if result['data'] else 0
    print(f"Months: {len(result['data'])}")
    print(f"Total orders: {total}")
    print(f"Total revenue: USD {revenue:.2f}")
    print("\nMonthly breakdown:")
    for m in result['data']:
        print(f"  {m['month']}: {m['orders']} orders, USD {m['revenue']:.2f}")
else:
    print(f"Error: {result.get('reason', 'unknown')}")
