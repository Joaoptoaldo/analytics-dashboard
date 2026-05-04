#!/usr/bin/env python3
"""AUDITORIA TÉCNICA SEVERA - LOOP 2 VALIDAÇÃO SEMÂNTICA"""
import requests
import os

os.environ['ENV'] = 'development'
os.environ['ALLOW_SEED'] = 'true'

from backend.db import SessionLocal
from backend.models.product import Product
from sqlalchemy import func

BASE_URL = 'http://127.0.0.1:8000/api'

print('╔' + '═' * 118 + '╗')
print('║' + ' ' * 35 + 'AUDITORIA TÉCNICA SEVERA - LOOP 2 VALIDAÇÃO SEMÂNTICA' + ' ' * 29 + '║')
print('╚' + '═' * 118 + '╝')

print('\n📋 TESTE 1: Verificar que nenhum dado sintético está visível no API')
print('─' * 120)

db = SessionLocal()
try:
    # Get synthetic data count from DB
    synthetic_count = db.query(func.count(Product.id)).filter(Product.is_synthetic == True).scalar() or 0
    real_count = db.query(func.count(Product.id)).filter(Product.is_synthetic == False).scalar() or 0
    
    print(f'DB: {synthetic_count} synthetic records, {real_count} real records')
    
    # Check /api/overview
    r = requests.get(f'{BASE_URL}/overview?period=all', timeout=5)
    api_total = r.json().get('total_orders', 0)
    
    if api_total == real_count:
        print(f'✅ API /overview retorna {api_total} pedidos (matches {real_count} real records)')
        test1_pass = True
    else:
        print(f'❌ API /overview retorna {api_total}, expected {real_count}')
        test1_pass = False

finally:
    db.close()

print()
print('📋 TESTE 2: Verificar categorias (sem A, B, C - placeholder)')
print('─' * 120)

try:
    r = requests.get(f'{BASE_URL}/distribution/category', timeout=5)
    data = r.json()
    
    if data.get('state') == 'valid':
        categories = [c['category'] for c in data.get('data', [])]
        
        # Check for placeholder categories
        placeholder_cats = [c for c in categories if c in ['A', 'B', 'C', 'Categoria A', 'Categoria B', 'Categoria C']]
        
        print(f'Categories: {categories}')
        
        if not placeholder_cats:
            print(f'✅ Nenhuma categoria placeholder detectada')
            test2_pass = True
        else:
            print(f'❌ Categorias placeholder encontradas: {placeholder_cats}')
            test2_pass = False
    else:
        print('❌ API retornou estado inválido')
        test2_pass = False
except Exception as e:
    print(f'❌ Erro: {e}')
    test2_pass = False

print()
print('📋 TESTE 3: Verificar produtos top (sem client_0, client_1 - placeholder)')
print('─' * 120)

try:
    r = requests.get(f'{BASE_URL}/top/products?limit=10', timeout=5)
    data = r.json()
    
    if data.get('state') == 'valid':
        products = [p['product_name'] for p in data.get('data', [])]
        
        # Check for placeholder products
        placeholder_prods = [p for p in products if p.startswith('client_') or p.startswith('product_')]
        
        print(f'Top 3 products: {products[:3]}')
        
        if not placeholder_prods:
            print(f'✅ Nenhum produto placeholder detectado')
            test3_pass = True
        else:
            print(f'❌ Produtos placeholder encontrados: {placeholder_prods}')
            test3_pass = False
    else:
        print('❌ API retornou estado inválido')
        test3_pass = False
except Exception as e:
    print(f'❌ Erro: {e}')
    test3_pass = False

print()
print('📋 TESTE 4: Verificar que sales/monthly filtra dados sintéticos')
print('─' * 120)

try:
    r = requests.get(f'{BASE_URL}/sales/monthly', timeout=5)
    data = r.json()
    
    if data.get('state') == 'valid':
        months = data.get('data', [])
        total_from_monthly = sum(m['orders'] for m in months)
        
        db = SessionLocal()
        expected_total = db.query(func.count(Product.id)).filter(Product.is_synthetic == False).scalar() or 0
        db.close()
        
        print(f'Monthly data sum: {total_from_monthly}, Expected (real records only): {expected_total}')
        
        if total_from_monthly == expected_total:
            print(f'✅ sales/monthly retorna apenas dados reais')
            test4_pass = True
        else:
            print(f'❌ Divergência: {total_from_monthly} != {expected_total}')
            test4_pass = False
    else:
        print('❌ API retornou estado inválido')
        test4_pass = False
except Exception as e:
    print(f'❌ Erro: {e}')
    test4_pass = False

print()
print('╔' + '═' * 118 + '╗')
if test1_pass and test2_pass and test3_pass and test4_pass:
    print('║' + ' ' * 42 + '✅ LOOP 2 RESULTADO: TODOS OS TESTES PASSARAM ✅' + ' ' * 26 + '║')
    print('║' + ' ' * 35 + 'Dashboard contém APENAS dados semânticos válidos' + ' ' * 37 + '║')
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
    print('║' + ' ' * 45 + f'❌ LOOP 2 FALHOU: {", ".join(failed)}' + ' ' * (29 - len(", ".join(failed))) + '║')
print('╚' + '═' * 118 + '╝')
