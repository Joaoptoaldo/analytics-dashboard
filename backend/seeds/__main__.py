import logging
import os
import sys

from backend.seeds.seed_data import seed_database


def main():
    """_summary_: Executa o seed manual com protecoes para evitar uso indevido
    """
    ENV = os.getenv("ENV", "production")
    ALLOW_SEED = os.getenv("ALLOW_SEED", "false").lower() == "true"
    # Exige argumento CLI explicito
    if len(sys.argv) < 2 or sys.argv[1] != "--confirm-seed":
        print("[ERRO] Execucao do seed requer argumento explicito: --confirm-seed")
        exit(2)
    if ENV != "development":
        print("[ERRO] Seed so pode ser executado em ambiente de desenvolvimento (ENV=development)")
        exit(1)
    if not ALLOW_SEED:
        print("[ERRO] Seed bloqueado: defina ALLOW_SEED=true no ambiente")
        exit(3)
    logging.basicConfig(level=logging.CRITICAL)
    logging.critical("[CRITICAL] Seed executado manualmente em ambiente de desenvolvimento!")
    print("[INFO] Populando banco de dados com dados ficticios...")
    seed_database()
    print("[OK] Banco populado com seed.")


if __name__ == "__main__":
    main()
