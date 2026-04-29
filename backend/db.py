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
        from backend.models.product import Product  # noqa: F401
    except Exception:
        pass
    Base.metadata.create_all(bind=engine)

print("Database URL:", DATABASE_URL)