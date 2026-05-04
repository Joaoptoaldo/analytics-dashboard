#!/usr/bin/env python3
"""AUDITORIA TÉCNICA SEVERA - Loop 1: Validação Aritmética"""
import requests
import json

BASE_URL = 'http://127.0.0.1:8000/api'

print('=' * 80)
print('LOOP 1: VALIDAÇÃO ARITMÉTICA - API vs SQL')
print('=' * 80)

# Ground truth
sql_data = {
    'total_orders': 53,
    'total_revenue': 117970.71,
    'total_customers': 26,
    'conversion_rate': 22.64,
    'avg_order_value': 2225.86
}

print('\n[BASELINE] Ground Truth (SQL Direct Query):')
for key, val in sql_data.items():
    if 'revenue' in key or 'value' in key:
        print(f'  {key}: USD {val:.2f}')
    elif 'rate' in key:
        print(f'  {key}: {val:.2f}%')
    else:
        print(f'  {key}: {val}')

# API Data
print('\n[API DATA] Fetching from /api/overview...')
try:
    r = requests.get(f'{BASE_URL}/overview?period=all', timeout=5)
    api_data = r.json()
    
    comparisons = [
        ('Total Orders', 'total_orders', sql_data['total_orders'], api_data.get('total_orders')),
        ('Total Revenue', 'total_revenue', sql_data['total_revenue'], api_data.get('total_revenue')),
        ('Total Customers', 'total_customers', sql_data['total_customers'], api_data.get('total_customers')),
        ('Conversion Rate', 'conversion_rate', sql_data['conversion_rate'], api_data.get('conversion_rate')),
    ]
    
    print('\n' + '=' * 80)
    print('COMPARISON TABLE: SQL vs API')
    print('=' * 80)
    print(f'{"Metric":<25} {"SQL (Truth)":<25} {"API":<25} {"Status":<10}')
    print('-' * 80)
    
    all_match = True
    for name, key, sql_val, api_val in comparisons:
        if api_val is None:
            status = '❌ MISSING'
            all_match = False
        elif isinstance(sql_val, float):
            match = abs(sql_val - api_val) < 0.01
            status = '✅ MATCH' if match else '❌ DIFFER'
            if not match:
                all_match = False
                diff = abs(sql_val - api_val)
                pct = (diff / sql_val * 100) if sql_val != 0 else 0
                print(f'{name:<25} {sql_val:<25.2f} {api_val:<25.2f} {status:<10} (diff: {diff:.2f}, {pct:.1f}%)')
                continue
        else:
            match = sql_val == api_val
            status = '✅ MATCH' if match else '❌ DIFFER'
            if not match:
                all_match = False
        
        if isinstance(sql_val, float):
            print(f'{name:<25} {sql_val:<25.2f} {api_val:<25.2f} {status:<10}')
        else:
            print(f'{name:<25} {str(sql_val):<25} {str(api_val):<25} {status:<10}')
    
    print('=' * 80)
    if all_match:
        print('✅ LOOP 1 RESULT: ALL METRICS MATCH ✅')
    else:
        print('❌ LOOP 1 RESULT: DIVERGENCES DETECTED ❌')

except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
