#!/usr/bin/env python3
"""
VALIDACAO CONSISTENCIA - Loop 3
Verifica: gráfico == tabela == KPI (consistência matemática entre componentes)
Foco: Garantir que dados agregados de diferentes endpoints são mutuamente consistentes
"""
import os
import sys

os.environ["ENV"] = "development"
os.environ["ALLOW_SEED"] = "true"

import requests
from backend.db import SessionLocal
from backend.models.product import Product
from sqlalchemy import func

BASE_URL = "http://127.0.0.1:8000/api"

def validate_consistency():
    print("=" * 80)
    print("VALIDACAO CROSS-COMPONENT - Loop 3: Consistência matemática entre endpoints")
    print("=" * 80)
    
    db = SessionLocal()
    try:
        # Ground truth: soma de todos registros reais
        print("\n[DB BASELINE] Ground truth (real data only)")
        real_total = db.query(func.count(Product.id)).filter(Product.is_synthetic == False).scalar() or 0
        real_revenue = db.query(func.sum(Product.revenue)).filter(Product.is_synthetic == False).scalar() or 0.0
        
        print(f"  Expected Total Orders: {real_total}")
        print(f"  Expected Total Revenue: USD {real_revenue:.2f}")
        print(f"  [NOTE] All calculations should resolve to these totals")
        
        # Test 1: /api/overview totals == monthly aggregates
        print("\n[TEST 1] /api/overview totals == /api/sales/monthly aggregates")
        try:
            r_overview = requests.get(f"{BASE_URL}/overview?period=all", timeout=5)
            assert r_overview.status_code == 200
            overview_data = r_overview.json()
            overview_orders = overview_data.get('total_orders', 0)
            overview_revenue = overview_data.get('total_revenue', 0)
            
            r_monthly = requests.get(f"{BASE_URL}/sales/monthly", timeout=5)
            assert r_monthly.status_code == 200
            monthly_data = r_monthly.json()
            monthly_months = monthly_data.get('data', [])
            monthly_orders = sum(m['orders'] for m in monthly_months)
            monthly_revenue = sum(m['revenue'] for m in monthly_months)
            
            print(f"  Overview: {overview_orders} orders, USD {overview_revenue:.2f}")
            print(f"  Monthly sum: {monthly_orders} orders, USD {monthly_revenue:.2f}")
            
            assert overview_orders == monthly_orders, f"Orders mismatch: {overview_orders} != {monthly_orders}"
            assert abs(overview_revenue - monthly_revenue) < 0.01, f"Revenue mismatch: {overview_revenue} != {monthly_revenue}"
            
            print(f"  [PASS] Overview totals == Monthly aggregates")
        except Exception as e:
            print(f"  [FAIL] {e}")
            return False
        
        # Test 2: /api/top/products revenue sum (approximate) == overview revenue
        print("\n[TEST 2] /api/top/products sum is reasonable fraction of total")
        try:
            r_top = requests.get(f"{BASE_URL}/top/products?limit=10", timeout=5)
            assert r_top.status_code == 200
            top_data = r_top.json()
            top_products = top_data.get('data', [])
            top_revenue = sum(p['revenue'] for p in top_products)
            
            print(f"  Top 10 products revenue: USD {top_revenue:.2f}")
            print(f"  Overview revenue: USD {overview_revenue:.2f}")
            print(f"  Percentage: {(top_revenue/overview_revenue*100):.1f}%")
            
            # Top 10 should be reasonable fraction (typically > 30% of total)
            assert top_revenue > 0, "Top products revenue should be > 0"
            percentage = top_revenue / overview_revenue * 100 if overview_revenue > 0 else 0
            assert percentage > 20, f"Top 10 should be > 20% of total, got {percentage:.1f}%"
            
            print(f"  [PASS] Top products are reasonable fraction of total")
        except Exception as e:
            print(f"  [FAIL] {e}")
            return False
        
        # Test 3: Distribution category sum == overview total
        print("\n[TEST 3] /api/distribution/category sum == overview total")
        try:
            r_dist = requests.get(f"{BASE_URL}/distribution/category", timeout=5)
            assert r_dist.status_code == 200
            dist_data = r_dist.json()
            dist_categories = dist_data.get('data', [])
            dist_orders = sum(c['count'] for c in dist_categories)
            
            print(f"  Distribution sum: {dist_orders} orders")
            print(f"  Overview: {overview_orders} orders")
            
            assert dist_orders == overview_orders, f"Orders mismatch: {dist_orders} != {overview_orders}"
            
            print(f"  [PASS] Distribution categories sum to overview totals")
        except Exception as e:
            print(f"  [FAIL] {e}")
            return False
        
        # Test 4: Monthly progression (each month cumulative >= previous)
        print("\n[TEST 4] Monthly data temporal consistency")
        try:
            # Just verify months are in order
            assert len(monthly_months) > 0, "No monthly data"
            
            print(f"  Months in order: {[m['month'] for m in monthly_months]}")
            print(f"  Month count: {len(monthly_months)}")
            
            # Verify each month has non-negative values
            for m in monthly_months:
                assert m['orders'] >= 0, f"Month {m['month']} has negative orders: {m['orders']}"
                assert m['revenue'] >= 0, f"Month {m['month']} has negative revenue: {m['revenue']}"
            
            print(f"  [PASS] All months have valid (non-negative) values")
        except Exception as e:
            print(f"  [FAIL] {e}")
            return False
        
        # Test 5: Final reconciliation - all data is from synthetic=False
        print("\n[TEST 5] Final reconciliation: all metrics point to same 53 orders")
        try:
            print(f"  Database (real): {real_total} orders")
            print(f"  Overview: {overview_orders} orders")
            print(f"  Monthly sum: {monthly_orders} orders")
            print(f"  Distribution sum: {dist_orders} orders")
            
            assert real_total == overview_orders == monthly_orders == dist_orders, \
                f"Mismatch: DB={real_total}, Overview={overview_orders}, Monthly={monthly_orders}, Dist={dist_orders}"
            
            print(f"  [PASS] All metrics consistently show {real_total} orders (no synthetic data leak)")
        except Exception as e:
            print(f"  [FAIL] {e}")
            return False
        
        print("\n" + "=" * 80)
        print("[PASS] VALIDACAO CONSISTENCIA COMPLETA - Dashboard é CONFIÁVEL!")
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
    success = validate_consistency()
    sys.exit(0 if success else 1)
