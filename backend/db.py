import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# IMPORTANTE: Não usar fallback silencioso para DATABASE_URL
# Importar config validado (vai falhar se DATABASE_URL inválido)
from backend.config import DATABASE_URL

# DATABASE_URL já foi validado em backend/config.py
# Se chegou aqui, está OK para usar
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL não pode ser None. "
        "Verifique backend/config.py para validação de variáveis de ambiente."
    )

# Configuração do engine para PostgreSQL (produção) ou SQLite (desenvolvimento validado)
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()



def init_db():
    try:
        from backend.models.product import Product
        from backend.models.sync_state import SyncState
    except Exception:
        pass
    Base.metadata.create_all(bind=engine)

    # Seed controlado por variável de ambiente
    ENV = os.getenv("ENV", "production")
    if ENV == "development":
       
        from backend.seeds.seed_data import seed_database
        print("[INFO] Ambiente de desenvolvimento detectado. Para popular o banco com seed, execute manualmente: backend/seeds/seed_data.py")
