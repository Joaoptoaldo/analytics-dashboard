"""
Configuration Validation Module — Production-Grade Config Management

Este módulo implementa validação obrigatória de variáveis de ambiente,
com fail-fast para garantir deploy seguro em produção.

Princípios:
1. Nenhum fallback silencioso em PROD
2. Validação no startup (antes de qualquer lógica)
3. Diferenças explícitas entre DEV e PROD
4. Erros claros e acionáveis
"""

import logging
import os
import sys
from typing import Literal

from dotenv import load_dotenv

# Carregar .env antes de qualquer leitura de ambiente.
load_dotenv()

# Configurar logging ANTES de tudo
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================================
# Environment Detection
# ============================================================================

ENV = os.getenv("ENV", "production").lower().strip()
IS_PRODUCTION = ENV == "production"
IS_DEVELOPMENT = ENV == "development"
ALLOWED_ENVS = {"development", "production"}

# ============================================================================
# Required Configuration Variables
# ============================================================================

class ConfigError(Exception):
    """Exceção levantada quando configuração é inválida"""
    pass


class ConfigValidator:
    """Validador de configuração com regras DEV vs PROD"""

    def __init__(self, env: str):
        self.env = env.lower()
        self.is_prod = self.env == "production"
        self.errors: list[str] = []
        self.warnings: list[str] = []

        if self.env not in ALLOWED_ENVS:
            self.errors.append(
                f"ENV inválido: {self.env}. Valores aceitos: development, production."
            )

    def validate_database_url(self) -> str:
        """
        DATABASE_URL é OBRIGATÓRIO.
        
        PROD: aceita PostgreSQL (postgresql://, postgres://) e rejeita SQLite
        DEV: Pode ser SQLite, mas adverte se não PostgreSQL
        """
        database_url = os.getenv("DATABASE_URL")

        if not database_url or not database_url.strip():
            self.errors.append(
                "DATABASE_URL não configurado. "
                "Em PROD: use PostgreSQL (postgresql://...). "
                "Em DEV: pode usar SQLite (sqlite:///./backend.db)."
            )
            return None

        database_url = database_url.strip()

        if self.is_prod:
            scheme = database_url.split("://", 1)[0].lower()

            if scheme.startswith("sqlite"):
                self.errors.append(
                    "DATABASE_URL inválido para PROD. SQLite não é permitido em produção."
                )
                return None

            if not scheme.startswith("postgres"):
                self.errors.append(
                    f"DATABASE_URL inválido para PROD. Esperado PostgreSQL (postgres:// ou postgresql://), "
                    f"mas recebeu um esquema não suportado."
                )
                return None

            # Validações adicionais para PostgreSQL
            if "@" not in database_url:
                self.errors.append(
                    f"DATABASE_URL incompleto: falta credenciais. "
                    f"Formato: postgresql://user:password@host:port/database"
                )
                return None

        else:  # DEV
            if database_url.startswith("sqlite"):
                self.warnings.append(
                    "DATABASE_URL é SQLite (DEV OK). Em PROD, use PostgreSQL."
                )
            elif not database_url.startswith("postgresql://"):
                self.warnings.append(
                    "DATABASE_URL tipo desconhecido no ambiente atual."
                )

        return database_url

    def validate_cors_origins(self) -> list[str]:
        """
        CORS_ORIGINS é OBRIGATÓRIO.
        
        PROD: MUST ser whitelist explícita (não "*", não localhost)
        DEV: Pode ter localhost
        """
        cors_origins_str = os.getenv("CORS_ORIGINS")

        if not cors_origins_str or not cors_origins_str.strip():
            self.errors.append(
                "CORS_ORIGINS não configurado. "
                "Deve ser lista de domínios separados por vírgula. "
                "Ex: https://dashboard.example.com,https://www.dashboard.example.com"
            )
            return []

        cors_origins = [o.strip() for o in cors_origins_str.split(",") if o.strip()]

        if not cors_origins:
            self.errors.append("CORS_ORIGINS vazio após parsing")
            return []

        if self.is_prod:
            # Validações PROD
            if "*" in cors_origins:
                self.errors.append(
                    "CORS_ORIGINS contém '*' em PROD. "
                    "Não permitido por razões de segurança. "
                    "Use whitelist explícita."
                )
                return []

            localhost_origins = [o for o in cors_origins if "localhost" in o or "127.0.0.1" in o]
            if localhost_origins:
                self.errors.append(
                    f"CORS_ORIGINS contém localhost em PROD: {localhost_origins}. "
                    f"Use apenas domínios de produção."
                )
                return []

            # Validar HTTPS
            non_https = [o for o in cors_origins if not o.startswith("https://") and not o.startswith("http://localhost")]
            if non_https:
                self.warnings.append(
                    f"CORS_ORIGINS contém URLs sem HTTPS em PROD: {non_https}. "
                    f"Recomendado usar HTTPS."
                )

        else:  # DEV
            if "*" in cors_origins:
                self.warnings.append(
                    "CORS_ORIGINS contém '*' (aceito em DEV, não em PROD)"
                )

        return cors_origins

    def validate_external_sync_token(self) -> str | None:
        """
        EXTERNAL_SYNC_TOKEN é RECOMENDADO em PROD.
        
        PROD: DEVE ser definido (protege /internal/external-products/sync)
        DEV: Pode ser vazio (endpoint retornará 500, ok para testes)
        """
        token = os.getenv("EXTERNAL_SYNC_TOKEN", "").strip()

        if self.is_prod and not token:
            self.errors.append(
                "EXTERNAL_SYNC_TOKEN não configurado em PROD. Configure um token seguro com 32+ chars."
            )
            return None

        if self.is_prod and token and len(token) < 32:
            self.errors.append(
                f"EXTERNAL_SYNC_TOKEN muito curto ({len(token)} chars). Em PROD são exigidos 32+ chars."
            )
            return None

        if token and len(token) < 16:
            self.warnings.append(
                f"EXTERNAL_SYNC_TOKEN muito curto ({len(token)} chars). "
                f"Recomendado 32+ chars para segurança."
            )

        return token if token else None

    def validate_allow_seed(self) -> bool:
        """
        ALLOW_SEED controla se dados de seed sobrescrevem database.
        
        PROD: DEVE ser false
        DEV: Pode ser true ou false
        """
        allow_seed_str = os.getenv("ALLOW_SEED", "false").lower()
        allow_seed = allow_seed_str in ("true", "1", "yes")

        if self.is_prod and allow_seed:
            self.errors.append(
                "ALLOW_SEED=true em PROD é PERIGOSO. "
                "Pode sobrescrever dados de produção. "
                "DEVE ser false."
            )
            return False

        return allow_seed

    def validate(self) -> dict:
        """Executa todas as validações"""
        logger.info(f"[CONFIG] Validando configuração para ENV={self.env}...")

        config = {
            "env": self.env,
            "is_production": self.is_prod,
            "database_url": self.validate_database_url(),
            "cors_origins": self.validate_cors_origins(),
            "external_sync_token": self.validate_external_sync_token(),
            "allow_seed": self.validate_allow_seed(),
        }

        # Exibir warnings (não bloqueiam)
        if self.warnings:
            logger.warning(f"[CONFIG] {len(self.warnings)} warnings encontrados:")
            for warning in self.warnings:
                logger.warning(f"  ⚠️  {warning}")

        # Exibir erros e falhar se houver
        if self.errors:
            logger.error(f"[CONFIG] {len(self.errors)} erros críticos encontrados:")
            for error in self.errors:
                logger.error(f"  ❌ {error}")

            raise ConfigError(
                f"Configuração inválida para {self.env}. "
                f"Verifique variáveis de ambiente e tente novamente."
            )

        logger.info("[CONFIG] ✅ Configuração validada com sucesso!")
        return config


def load_and_validate_config() -> dict:
    """
    Carrega e valida configuração global.
    
    Lançar ConfigError se inválido (bloqueia startup).
    """
    try:
        validator = ConfigValidator(ENV)
        config = validator.validate()
        return config
    except ConfigError as e:
        logger.error(f"[STARTUP] FALHA NA VALIDAÇÃO DE CONFIG: {e}")
        logger.error("[STARTUP] Sistema bloqueado. Corrija variáveis de ambiente e reinicie.")
        sys.exit(1)


# ============================================================================
# Global Config (loaded at startup)
# ============================================================================

try:
    # Carregar config no import (fail-fast)
    GLOBAL_CONFIG = load_and_validate_config()

    # Expor variáveis validadas
    DATABASE_URL = GLOBAL_CONFIG["database_url"]
    CORS_ORIGINS = GLOBAL_CONFIG["cors_origins"]
    EXTERNAL_SYNC_TOKEN = GLOBAL_CONFIG["external_sync_token"]
    ALLOW_SEED = GLOBAL_CONFIG["allow_seed"]

except ConfigError:
    # Se falhar aqui, o módulo não pode ser importado
    # Isso causa erro no startup do FastAPI
    raise
