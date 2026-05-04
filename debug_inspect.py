#!/usr/bin/env python3
"""Debug: Inspecionar qual get_sales_monthly está sendo usado"""
import os
os.environ["ENV"] = "development"
os.environ["ALLOW_SEED"] = "true"

import inspect
from backend.services.analytics import get_sales_monthly

# Obter o arquivo de source
source_file = inspect.getfile(get_sales_monthly)
print(f"Function located at: {source_file}")

# Obter as linhas de source
source_lines = inspect.getsource(get_sales_monthly)
print(f"\nFirst 20 lines of source:")
for i, line in enumerate(source_lines.split('\n')[:20]):
    print(f"{i+105}: {line}")  # Assuming starts at ~line 105

# Verificar se tem o filtro is_synthetic
if "is_synthetic == False" in source_lines:
    print("\n✓ Filtro is_synthetic encontrado no código source")
else:
    print("\n✗ PROBLEMA: Filtro is_synthetic NÃO encontrado no código source")
