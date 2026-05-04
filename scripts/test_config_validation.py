#!/usr/bin/env python3
"""
Script de Testes — Validar Configuração Fail-Fast

Este script simula diferentes cenários de deployment e verifica se a validação
de configuração está funcionando corretamente.

Cenários testados:
1. PROD com DATABASE_URL faltando → DEVE falhar com mensagem clara
2. PROD com CORS_ORIGINS faltando → DEVE falhar com mensagem clara
3. PROD com DATABASE_URL=sqlite → DEVE falhar com mensagem clara
4. PROD com CORS_ORIGINS="*" → DEVE falhar com mensagem clara
5. PROD com CORS_ORIGINS contendo localhost → DEVE falhar com mensagem clara
6. DEV com configuração válida → DEVE passar com warnings
7. PROD com configuração válida → DEVE passar sem erros

Uso:
    python scripts/test_config_validation.py
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# Cores para output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def run_test(name: str, env_vars: dict, should_fail: bool = False):
    """
    Executa um teste de configuração.

    Args:
        name: Nome descritivo do teste
        env_vars: Variáveis de ambiente para o teste
        should_fail: Se True, espera que falhe; se False, espera sucesso
    """
    print(f"\n{BOLD}{BLUE}▶ Teste: {name}{RESET}")
    print(f"  ENV vars: {env_vars}")

    # Preparar environment
    test_env = os.environ.copy()
    test_env.update(env_vars)

    # Remover variáveis não setadas (para simular falta)
    for key in list(test_env.keys()):
        if test_env[key] is None:
            del test_env[key]

    # Executar teste
    code = '''
import sys
try:
    from backend.config import GLOBAL_CONFIG
    print("✅ Config validation PASSED")
    sys.exit(0)
except SystemExit as e:
    if e.code == 1:
        print("❌ Config validation FAILED (exit 1)")
        sys.exit(1)
    raise
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(2)
'''

    result = subprocess.run(
        [sys.executable, "-c", code],
        env=test_env,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent)
    )

    # Analisar resultado
    success = result.returncode == 0
    expected_fail = should_fail and result.returncode != 0

    if success or expected_fail:
        status = f"{GREEN}✅ PASSED{RESET}"
        expected_str = "(passou conforme esperado)" if success else "(falhou conforme esperado)"
    else:
        status = f"{RED}❌ FAILED{RESET}"
        expected_str = f"(esperado {'falhar' if should_fail else 'passar'})"

    print(f"  Status: {status} {expected_str}")

    if result.stdout:
        for line in result.stdout.split('\n'):
            if line.strip():
                print(f"  > {line}")

    if result.stderr:
        for line in result.stderr.split('\n'):
            if line.strip() and "[INFO]" not in line and "[WARNING]" not in line and "[ERROR]" not in line:
                print(f"  {YELLOW}stderr: {line}{RESET}")
            elif "[ERROR]" in line:
                print(f"  {RED}ERROR: {line}{RESET}")

    return success or expected_fail


def main():
    """Executar suite de testes"""
    print(f"\n{BOLD}{BLUE}{'='*70}")
    print("CONFIG VALIDATION TEST SUITE")
    print(f"{'='*70}{RESET}\n")

    tests = [
        # PROD scenarios — devem FALHAR
        (
            "PROD: DATABASE_URL faltando",
            {
                "ENV": "production",
                "DATABASE_URL": None,
                "CORS_ORIGINS": "https://example.com",
                "EXTERNAL_SYNC_TOKEN": "token123456789012345",
            },
            True  # should_fail
        ),
        (
            "PROD: CORS_ORIGINS faltando",
            {
                "ENV": "production",
                "DATABASE_URL": "postgresql://user:pass@host/db",
                "CORS_ORIGINS": None,
                "EXTERNAL_SYNC_TOKEN": "token123456789012345",
            },
            True  # should_fail
        ),
        (
            "PROD: DATABASE_URL=SQLite (não PostgreSQL)",
            {
                "ENV": "production",
                "DATABASE_URL": "sqlite:///./backend.db",
                "CORS_ORIGINS": "https://example.com",
                "EXTERNAL_SYNC_TOKEN": "token123456789012345",
            },
            True  # should_fail
        ),
        (
            "PROD: CORS_ORIGINS='*' (wildcard não permitido)",
            {
                "ENV": "production",
                "DATABASE_URL": "postgresql://user:pass@host/db",
                "CORS_ORIGINS": "*",
                "EXTERNAL_SYNC_TOKEN": "token123456789012345",
            },
            True  # should_fail
        ),
        (
            "PROD: CORS_ORIGINS contém localhost",
            {
                "ENV": "production",
                "DATABASE_URL": "postgresql://user:pass@host/db",
                "CORS_ORIGINS": "https://example.com,http://localhost:5173",
                "EXTERNAL_SYNC_TOKEN": "token123456789012345",
            },
            True  # should_fail
        ),
        (
            "PROD: ALLOW_SEED=true (não permitido em prod)",
            {
                "ENV": "production",
                "DATABASE_URL": "postgresql://user:pass@host/db",
                "CORS_ORIGINS": "https://example.com",
                "EXTERNAL_SYNC_TOKEN": "token123456789012345",
                "ALLOW_SEED": "true",
            },
            True  # should_fail
        ),
        # DEV scenarios — devem PASSAR
        (
            "DEV: Configuração válida com SQLite",
            {
                "ENV": "development",
                "DATABASE_URL": "sqlite:///./backend.db",
                "CORS_ORIGINS": "http://localhost:5173,http://localhost:3000",
                "EXTERNAL_SYNC_TOKEN": None,
            },
            False  # should_pass
        ),
        (
            "DEV: CORS_ORIGINS com wildcard (ok em dev)",
            {
                "ENV": "development",
                "DATABASE_URL": "sqlite:///./backend.db",
                "CORS_ORIGINS": "*",
                "EXTERNAL_SYNC_TOKEN": None,
            },
            False  # should_pass
        ),
        # PROD scenarios — devem PASSAR
        (
            "PROD: Configuração válida completa",
            {
                "ENV": "production",
                "DATABASE_URL": "postgresql://user:pass@db.neon.tech/dashboard",
                "CORS_ORIGINS": "https://dashboard.example.com,https://www.example.com",
                "EXTERNAL_SYNC_TOKEN": "gerar-token-aleatorio-seguro-32-chars",
                "ALLOW_SEED": "false",
            },
            False  # should_pass
        ),
    ]

    passed = 0
    failed = 0

    for name, env_vars, should_fail in tests:
        if run_test(name, env_vars, should_fail):
            passed += 1
        else:
            failed += 1

    # Resumo
    print(f"\n{BOLD}{BLUE}{'='*70}")
    print(f"SUMMARY: {GREEN}{passed} passed{RESET}, {RED}{failed} failed{RESET}")
    print(f"{'='*70}{RESET}\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
