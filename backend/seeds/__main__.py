import os
from backend.seeds.seed_data import seed_database

if __name__ == "__main__":
    ENV = os.getenv("ENV", "production")
    if ENV != "development":
        print("[ERRO] Seed só pode ser executado em ambiente de desenvolvimento (ENV=development)")
        exit(1)
    print("[INFO] Populando banco de dados com dados fictícios...")
    seed_database()
    print("[OK] Banco populado com seed.")
