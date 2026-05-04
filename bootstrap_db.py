#!/usr/bin/env python3
"""
Bootstrap DB script:
- Remove arquivo BD antigo
- Cria schema novo
- Popula com seed (apenas dados reais, sem synthetic)
"""
import os
import sys
from pathlib import Path

# Setup environment
os.environ["ENV"] = "development"
os.environ["ALLOW_SEED"] = "true"

try:
    # Remove arquivo BD antigo se existir
    db_path = Path("backend.db")
    if db_path.exists():
        db_path.unlink()
        print(f"✓ Removido BD antigo: {db_path}")
    
    # Import depois de remover
    from backend.db import Base, engine, SessionLocal
    from backend.seeds.seed_data import seed_database
    
    # Criar schema
    Base.metadata.create_all(bind=engine)
    print("✓ Schema criado")
    
    # Executar seed
    seed_database()
    print("✓ Dados de seed inseridos")
    
    # Validação
    db = SessionLocal()
    try:
        from backend.models.product import Product
        from sqlalchemy import func
        
        total = db.query(func.count(Product.id)).scalar() or 0
        synthetic = db.query(func.count(Product.id)).filter(Product.is_synthetic == True).scalar() or 0
        real = db.query(func.count(Product.id)).filter(Product.is_synthetic == False).scalar() or 0
        
        print(f"\n✓ Validação:")
        print(f"  - Total records: {total}")
        print(f"  - Synthetic (from seed): {synthetic}")
        print(f"  - Real (from sync): {real}")
        print(f"\n✓ Bootstrap completo!")
    finally:
        db.close()

except Exception as e:
    print(f"✗ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
