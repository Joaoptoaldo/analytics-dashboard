import os
import sys
import re

ALLOWED_FILES = [
    'backend/seeds/seed_data.py',
    'backend/seeds/__main__.py',
    'backend/data.py',
]

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

ERRORS = []

for dirpath, _, filenames in os.walk(ROOT):
    for fname in filenames:
        if not fname.endswith('.py'):
            continue
        fpath = os.path.join(dirpath, fname)
        relpath = os.path.relpath(fpath, ROOT).replace('\\', '/')
        with open(fpath, encoding='utf-8') as f:
            content = f.read()
        if relpath not in ALLOWED_FILES:
            if re.search(r'\brandom\b', content):
                ERRORS.append(f'ERRO: Uso de random em {relpath}')
            if 'DATASET' in content:
                ERRORS.append(f'ERRO: Uso de DATASET em {relpath}')
            if re.search(r'def _build_seed_data', content):
                ERRORS.append(f'ERRO: Função de seed em {relpath}')

if ERRORS:
    print('Falha de hardening!')
    for err in ERRORS:
        print(err)
    sys.exit(1)
else:
    print('OK: Nenhum uso indevido de random, DATASET ou seed detectado.')
