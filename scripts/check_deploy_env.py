#!/usr/bin/env python3
"""Quick deploy validation: imports validated backend.config which enforces fail-fast rules."""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

try:
    from backend.config import GLOBAL_CONFIG
    print("OK: configuration validated for deploy:")
    for k, v in GLOBAL_CONFIG.items():
        print(f"- {k}: {v}")
    sys.exit(0)
except SystemExit as e:
    print("Config validation failed. Fix environment variables and try again.")
    sys.exit(1)
except Exception as e:
    print("Unexpected error while validating deploy config:", e)
    sys.exit(2)
