import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# IMPORTANTE: Não usar fallback silencioso para DATABASE_URL
# Importar config validado (vai falhar se DATABASE_URL inválido)
from backend.config import DATABASE_URL, IS_DEVELOPMENT

# DATABASE_URL já foi validado em backend/config.py
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL não pode ser None. "
        "Verifique backend/config.py para validação de variáveis de ambiente."
    )

# Configuração do engine para PostgreSQL (produção) ou SQLite (desenvolvimento validado)
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"connect_timeout": 5},
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()



def init_db():
    try:
        from backend.models.product import Product
        from backend.models.sync_state import SyncState
    except Exception:
        pass

    if IS_DEVELOPMENT:
        Base.metadata.create_all(bind=engine)
        logging.info(
            "[DB] Ambiente de desenvolvimento detectado. Para popular o banco com seed, execute manualmente: backend/seeds/seed_data.py"
        )
