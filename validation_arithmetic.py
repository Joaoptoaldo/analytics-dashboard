#!/usr/bin/env python3
"""
VALIDAÇÃO ARITMÉTICA - Loop 1
Verifica: API == SQL (sum, count, avg)
Foco: Garantir que filtros de is_synthetic=False funcionam corretamente
"""
import os
import sys
from pathlib import Path

os.environ["ENV"] = "development"
os.environ["ALLOW_SEED"] = "true"

from backend.db import SessionLocal
from backend.models.product import Product
from sqlalchemy import func

def validate_arithmetic():
    db = SessionLocal()
    try:
        print("=" * 80)
        print("VALIDACAO ARITMETICA - Loop 1: Backend Consistency")
        print("=" * 80)
        
        # Query 1: Todos os registros (sem filtro)
        print("\n[TEST 1] ALL RECORDS (sem filtro is_synthetic)")
        total_all = db.query(func.count(Product.id)).scalar() or 0
        revenue_all = db.query(func.sum(Product.revenue)).scalar() or 0.0
        print(f"  Total: {total_all} records")
        print(f"  Revenue: USD {revenue_all:.2f}")
        print(f"  Expected: 50 synthetic + 53 real = 103 total")
        assert total_all == 103, f"FALHOU: Expected 103, got {total_all}"
        print("  [PASS]")
        
        # Query 2: Apenas dados sínte ticos (is_synthetic=True)
        print("\n[TEST 2] SYNTHETIC ONLY (is_synthetic=True)")
        synthetic_count = db.query(func.count(Product.id)).filter(Product.is_synthetic == True).scalar() or 0
        synthetic_revenue = db.query(func.sum(Product.revenue)).filter(Product.is_synthetic == True).scalar() or 0.0
        print(f"  Synthetic count: {synthetic_count}")
        print(f"  Synthetic revenue: USD {synthetic_revenue:.2f}")
        print(f"  Expected: 50 records")
        assert synthetic_count == 50, f"FALHOU: Expected 50, got {synthetic_count}"
        print("  [PASS]")
        
        # Query 3: Apenas dados reais (is_synthetic=False)
        print("\n[TEST 3] REAL DATA ONLY (is_synthetic=False)")
        real_count = db.query(func.count(Product.id)).filter(Product.is_synthetic == False).scalar() or 0
        real_revenue = db.query(func.sum(Product.revenue)).filter(Product.is_synthetic == False).scalar() or 0.0
        print(f"  Real count: {real_count}")
        print(f"  Real revenue: USD {real_revenue:.2f}")
        print(f"  Expected: 53 records (demo)")
        assert real_count == 53, f"FALHOU: Expected 53, got {real_count}"
        print("  [PASS]")
        
        # Query 4: Soma de synthetic + real = total
        print("\n[TEST 4] INVARIANCIA (Synthetic + Real = Total)")
        assert synthetic_count + real_count == total_all, \
            f"FALHOU: {synthetic_count} + {real_count} != {total_all}"
        assert abs((synthetic_revenue + real_revenue) - revenue_all) < 0.01, \
            f"FALHOU: {synthetic_revenue} + {real_revenue} != {revenue_all}"
        print(f"  {synthetic_count} + {real_count} = {total_all} [OK]")
        print(f"  USD {synthetic_revenue:.2f} + USD {real_revenue:.2f} = USD {revenue_all:.2f} [OK]")
        print("  [PASS]")
        
        # Query 5: Distribuição por categoria (todos)
        print("\n[TEST 5] CATEGORIA DISTRIBUTION (synthetic + real)")
        cats_all = db.query(Product.category, func.count(Product.id).label('cnt')).group_by(Product.category).order_by(func.count(Product.id).desc()).all()
        print(f"  Categories found: {len(cats_all)}")
        total_cat = sum(c[1] for c in cats_all)
        print(f"  Total count across categories: {total_cat}")
        assert total_cat == total_all, f"FALHOU: {total_cat} != {total_all}"
        print("  [PASS]")
        
        # Query 6: Status distribution
        print("\n[TEST 6] STATUS DISTRIBUTION")
        statuses = db.query(Product.status, func.count(Product.id).label('cnt')).group_by(Product.status).order_by(func.count(Product.id).desc()).all()
        status_total = sum(s[1] for s in statuses)
        print(f"  Statuses found: {len(statuses)}")
        for st in statuses:
            print(f"    - {st[0]}: {st[1]} orders")
        assert status_total == total_all, f"FALHOU: {status_total} != {total_all}"
        print("  [PASS]")
        
        # Query 7: Operação de filtro em backend/main.py (_apply_db_filters)
        print("\n[TEST 7] BACKEND FILTER CONSISTENCY")
        print("  Testing: _apply_db_filters always adds is_synthetic=False")
        from backend.main import _apply_db_filters
        test_query = db.query(Product)
        filtered = _apply_db_filters(test_query, "all", "all", "all", "")
        filtered_count = filtered.with_entities(func.count(Product.id)).scalar() or 0
        print(f"  After _apply_db_filters('all'): {filtered_count} records")
        print(f"  Expected: 53 (real data only, no synthetic)")
        assert filtered_count == 53, f"FALHOU: Expected 53, got {filtered_count}"
        print("  [PASS] Correctly filters OUT synthetic data")
        
        print("\n" + "=" * 80)
        print("[PASS] VALIDACAO ARITMETICA COMPLETA - Todos os testes passaram!")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n[FAIL] ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = validate_arithmetic()
    sys.exit(0 if success else 1)
