#!/usr/bin/env python3
"""AUDITORIA TÉCNICA SEVERA - LOOP 3 VALIDAÇÃO DE CONSISTÊNCIA"""
import requests

BASE_URL = 'http://127.0.0.1:8000/api'

print('╔' + '═' * 118 + '╗')
print('║' + ' ' * 30 + 'AUDITORIA TÉCNICA SEVERA - LOOP 3 VALIDAÇÃO DE CONSISTÊNCIA SISTÊMICA' + ' ' * 18 + '║')
print('╚' + '═' * 118 + '╝')

# Get baseline from overview
try:
    r = requests.get(f'{BASE_URL}/overview?period=all', timeout=5)
    overview_data = r.json()
    baseline_orders = overview_data.get('total_orders', 0)
    baseline_revenue = overview_data.get('total_revenue', 0)
    baseline_customers = overview_data.get('total_customers', 0)
except Exception as e:
    print(f'❌ Erro ao obter baseline: {e}')
    exit(1)

print()
print('📋 TESTE 1: Consistência entre /overview e /sales/monthly')
print('─' * 120)

try:
    r = requests.get(f'{BASE_URL}/sales/monthly', timeout=5)
    monthly_data = r.json()
    
    if monthly_data.get('state') == 'valid':
        months = monthly_data.get('data', [])
        monthly_orders = sum(m['orders'] for m in months)
        monthly_revenue = sum(m['revenue'] for m in months)
        
        print(f'Overview: {baseline_orders} pedidos, USD {baseline_revenue:.2f}')
        print(f'Soma de sales/monthly: {monthly_orders} pedidos, USD {monthly_revenue:.2f}')
        
        orders_match = baseline_orders == monthly_orders
        revenue_match = abs(baseline_revenue - monthly_revenue) < 0.01
        
        if orders_match and revenue_match:
            print(f'✅ Dados consistentes entre /overview e /sales/monthly')
            test1_pass = True
        else:
            if not orders_match:
                print(f'❌ Pedidos divergem: {baseline_orders} != {monthly_orders}')
            if not revenue_match:
                diff = abs(baseline_revenue - monthly_revenue)
                print(f'❌ Receita diverge: diferença USD {diff:.2f}')
            test1_pass = False
    else:
        print('❌ API retornou estado inválido')
        test1_pass = False
except Exception as e:
    print(f'❌ Erro: {e}')
    test1_pass = False

print()
print('📋 TESTE 2: Consistência entre /distribution/category (total)')
print('─' * 120)

try:
    r = requests.get(f'{BASE_URL}/distribution/category', timeout=5)
    dist_data = r.json()
    
    if dist_data.get('state') == 'valid':
        categories = dist_data.get('data', [])
        dist_orders = sum(c['count'] for c in categories)
        
        print(f'Overview: {baseline_orders} pedidos')
        print(f'Soma de distribution/category: {dist_orders} pedidos')
        
        if baseline_orders == dist_orders:
            print(f'✅ Total de pedidos consistente')
            test2_pass = True
        else:
            print(f'❌ Pedidos divergem: {baseline_orders} != {dist_orders}')
            test2_pass = False
    else:
        print('❌ API retornou estado inválido')
        test2_pass = False
except Exception as e:
    print(f'❌ Erro: {e}')
    test2_pass = False

print()
print('📋 TESTE 3: Consistência entre /top/products (revenue)')
print('─' * 120)

try:
    r = requests.get(f'{BASE_URL}/top/products?limit=10', timeout=5)
    top_data = r.json()
    
    if top_data.get('state') == 'valid':
        products = top_data.get('data', [])
        top_revenue = sum(p['revenue'] for p in products)
        
        print(f'Overview Revenue: USD {baseline_revenue:.2f}')
        print(f'Top 10 products revenue: USD {top_revenue:.2f}')
        
        # Note: Top 10 products shouldn't sum to all revenue, so just check it's less than total
        if top_revenue <= baseline_revenue:
            print(f'✅ Top products revenue <= total revenue (expected)')
            test3_pass = True
        else:
            print(f'❌ Top products revenue > total revenue (invalid)')
            test3_pass = False
    else:
        print('❌ API retornou estado inválido')
        test3_pass = False
except Exception as e:
    print(f'❌ Erro: {e}')
    test3_pass = False

print()
print('📋 TESTE 4: Verificar que todos endpoints retornam estado=valid')
print('─' * 120)

endpoints = [
    '/overview?period=all',
    '/sales/monthly',
    '/distribution/category',
    '/top/products?limit=10'
]

all_valid = True
for endpoint in endpoints:
    try:
        r = requests.get(f'{BASE_URL}{endpoint}', timeout=5)
        data = r.json()
        state = data.get('state', 'unknown')
        
        if state == 'valid':
            print(f'  ✅ {endpoint}: estado={state}')
        else:
            print(f'  ❌ {endpoint}: estado={state}')
            all_valid = False
    except Exception as e:
        print(f'  ❌ {endpoint}: erro={e}')
        all_valid = False

test4_pass = all_valid

print()
print('📋 TESTE 5: Verificar que nenhum endpoint retorna NaN, null ou valores inválidos')
print('─' * 120)

endpoints_full = [
    ('/overview?period=all', ['total_orders', 'total_revenue', 'total_customers', 'conversion_rate']),
    ('/sales/monthly', ['data']),
    ('/distribution/category', ['data']),
    ('/top/products?limit=10', ['data'])
]

test5_pass = True
for endpoint, keys in endpoints_full:
    try:
        r = requests.get(f'{BASE_URL}{endpoint}', timeout=5)
        data = r.json()
        
        invalid_found = False
        for key in keys:
            value = data.get(key)
            
            # Check for NaN, None, empty (depending on context)
            if value is None:
                print(f'  ❌ {endpoint}: {key} = null')
                invalid_found = True
                test5_pass = False
            elif isinstance(value, float) and (value != value):  # NaN check
                print(f'  ❌ {endpoint}: {key} = NaN')
                invalid_found = True
                test5_pass = False
        
        if not invalid_found:
            print(f'  ✅ {endpoint}: todos valores válidos')
    except Exception as e:
        print(f'  ❌ {endpoint}: erro={e}')
        test5_pass = False

print()
print('╔' + '═' * 118 + '╗')

all_pass = test1_pass and test2_pass and test3_pass and test4_pass and test5_pass

if all_pass:
    print('║' + ' ' * 35 + '✅ LOOP 3 RESULTADO: TODOS OS TESTES PASSARAM ✅' + ' ' * 30 + '║')
    print('║' + ' ' * 28 + 'Todos endpoints mantêm consistência e integridade de dados' + ' ' * 32 + '║')
else:
    failed = []
    if not test1_pass:
        failed.append('TESTE 1')
    if not test2_pass:
        failed.append('TESTE 2')
    if not test3_pass:
        failed.append('TESTE 3')
    if not test4_pass:
        failed.append('TESTE 4')
    if not test5_pass:
        failed.append('TESTE 5')
    print('║' + ' ' * 45 + f'❌ LOOP 3 FALHOU: {", ".join(failed)}' + ' ' * (32 - len(", ".join(failed))) + '║')

print('╚' + '═' * 118 + '╝')
