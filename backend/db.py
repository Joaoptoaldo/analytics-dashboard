import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./backend.db")

# For SQLite we need `check_same_thread`; for Postgres (Neon) we must not pass it.
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()



def init_db():
    # Import models so they are registered on the metadata
    try:
        from backend.models.product import Product
    except Exception:
        pass
    Base.metadata.create_all(bind=engine)

    # Seed controlado por variável de ambiente
    ENV = os.getenv("ENV", "production")
    if ENV == "development":
        # O seed NUNCA roda automaticamente em produção!
        from backend.seeds.seed_data import seed_database
        print("[INFO] Ambiente de desenvolvimento detectado. Para popular o banco com seed, execute manualmente: backend/seeds/seed_data.py")

print("Database URL:", DATABASE_URL)