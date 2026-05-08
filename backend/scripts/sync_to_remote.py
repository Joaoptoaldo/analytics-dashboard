import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.db import SessionLocal, Base
from backend.models.product import Product


load_dotenv()


def get_remote_session(database_url: str):
    """_summary_: cria uma sessão SQLAlchemy para o banco de dados remoto, garantindo que a tabela de produtos exista no destino antes de retornar a sessão para uso

    Args:
        database_url (str): _description_: a URL de conexão do banco de dados remoto (ex: Postgres), que deve ser exportada na variável de ambiente `DATABASE_URL` antes de executar o script

    Returns:
        _type_: _description_: uma sessão SQLAlchemy conectada ao banco de dados remoto, pronta para ser usada para operações de leitura/escrita
    """
    engine = create_engine(database_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    # Garantir que tabela exista no destino
    Base.metadata.create_all(engine)
    return Session()


def sync_to_remote():
    """_summary_: sincroniza os produtos do banco local para o banco remoto, buscando todos os produtos locais, verificando se já existem no remoto (baseado em `external_id`), e atualizando ou inserindo conforme necessário, para garantir que os dados estejam alinhados entre os ambientes local e remoto

    Raises:
        RuntimeError: _description_: se a variável de ambiente `DATABASE_URL` não estiver definida, indicando que a URL do banco remoto não foi fornecida, o que é necessário para executar a sincronização
    """
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
