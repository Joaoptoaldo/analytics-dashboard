import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db import SessionLocal, Base
from backend.models.product import Product


load_dotenv()


def get_remote_session(database_url: str):
    engine = create_engine(database_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    # Garantir que tabela exista no destino
    Base.metadata.create_all(engine)
    return Session()


def sync_to_remote():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL não definida. Exporte a URL do Postgres antes de executar")

    local_db = SessionLocal()
    remote_db = get_remote_session(database_url)
    try:
        local_products = local_db.query(Product).all()
        print(f"Found {len(local_products)} products locally. Syncing to remote...")
        count = 0
        for p in local_products:
            if p.external_id:
                existing = remote_db.query(Product).filter_by(external_id=p.external_id).first()
            else:
                existing = None

            if existing:
                existing.client = p.client
                existing.category = p.category
                existing.revenue = p.revenue
                existing.status = p.status
                existing.region = p.region
                existing.date = p.date
            else:
                new = Product(
                    external_id=p.external_id,
                    client=p.client,
                    category=p.category,
                    revenue=p.revenue,
                    status=p.status,
                    region=p.region,
                    date=p.date,
                )
                remote_db.add(new)
            count += 1
        remote_db.commit()
        print(f"Synced {count} products to remote database.")
    finally:
        local_db.close()
        remote_db.close()


if __name__ == "__main__":
    sync_to_remote()
