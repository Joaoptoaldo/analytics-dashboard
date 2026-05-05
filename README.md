# Dashboard de Analise

Aplicacao full-stack para analise de indicadores de vendas com frontend em React/Vite e API em FastAPI.

O backend entrega metricas agregadas, filtros e listagem paginada de produtos. O frontend consome esses endpoints para montar dashboards, tabelas e graficos.

## Arquitetura Atual

- Frontend: React 19 + Vite + TypeScript, em src/, app/, components/, hooks/ e lib/
- Backend: FastAPI + SQLAlchemy, em backend/
- Banco: SQLite para desenvolvimento local e PostgreSQL em producao (obrigatorio quando ENV=production)
- Integracao externa: sincronizacao de produtos por endpoint interno protegido por token

Fluxo:
1. Frontend chama VITE_API_BASE_URL (deve terminar com /api).
2. Backend valida configuracao no startup (fail-fast).
3. Endpoints /api/* retornam dados para dashboard.
4. Endpoint /internal/external-products/sync executa sincronizacao externa com autenticacao por cabecalho x-internal-token.

## Requisitos

- Node.js 18+
- Python 3.11+
- pnpm (ou npm)

## Variaveis de Ambiente

### Backend (obrigatorias)

- ENV: development ou production
- DATABASE_URL: string de conexao do banco
- CORS_ORIGINS: lista separada por virgula
- ALLOW_SEED: true/false

### Backend (seguranca/operacao)

- EXTERNAL_SYNC_TOKEN: obrigatoria em production e com 32+ caracteres
- EXTERNAL_SYNC_MIN_INTERVAL_SECONDS: intervalo minimo entre syncs (padrao 60)

### Frontend

- VITE_API_BASE_URL: obrigatoria e deve terminar com /api
- VITE_EXTERNAL_SYNC_TOKEN: opcional (quando frontend aciona sync interno)
- VITE_USE_EXTERNAL: opcional

Exemplo local:

```env
# frontend
VITE_API_BASE_URL=http://localhost:8000/api
VITE_USE_EXTERNAL=true
VITE_EXTERNAL_SYNC_TOKEN=

# backend
ENV=development
DATABASE_URL=sqlite:///./backend.db
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
ALLOW_SEED=false
EXTERNAL_SYNC_TOKEN=
EXTERNAL_SYNC_MIN_INTERVAL_SECONDS=60
```

## Como Rodar Localmente

1. Instalar dependencias do frontend

```bash
pnpm install
```

2. Criar ambiente Python e instalar backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
```

3. Subir backend

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

4. Subir frontend

```bash
pnpm run dev
```

URLs locais:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000

## Endpoints Principais

### Health

- GET /health
- GET /readiness

### API principal (/api)

- GET /api/products
- GET /api/external-products
- GET /api/overview
- GET /api/filters
- GET /api/sales/monthly
- GET /api/sales/trend
- GET /api/distribution/category
- GET /api/top/products
- GET /api/metrics/ticket-average
- GET /api/customers/monthly
- GET /api/test-cors

### Endpoints legados ainda presentes

- GET /api/sales
- GET /api/category-distribution
- GET /api/category-revenue
- GET /api/activity
- GET /api/recent-orders

### Endpoint interno protegido

- POST /internal/external-products/sync
  - requer cabecalho x-internal-token
  - aplica rate-limit por EXTERNAL_SYNC_MIN_INTERVAL_SECONDS

## Deploy

### Render

- Arquivo de referencia: render.yaml
- Runtime: Docker
- Health check recomendado: /readiness
- Segredos esperados no provider:
  - DATABASE_URL
  - CORS_ORIGINS
  - EXTERNAL_SYNC_TOKEN
- Variaveis fixas comuns:
  - ENV=production
  - ALLOW_SEED=false

### Fly.io

- Arquivos de referencia: fly.toml e fly.toml.prod
- Build via Dockerfile
- Antes do deploy:
  1. Definir secrets reais (nao usar placeholders do fly.toml)
  2. Garantir DATABASE_URL PostgreSQL
  3. Garantir CORS_ORIGINS sem localhost e sem wildcard
  4. Garantir EXTERNAL_SYNC_TOKEN com 32+ chars
  5. Garantir ALLOW_SEED=false

## Documentacao e Scripts

- Documentacao operacional: docs/
  - docs/NEXT_STEPS_DEPLOY.md
  - docs/DEPLOY_CHECKLIST.md
  - docs/deploy-seguro.md
  - docs/runbook-rotacao-credenciais.md
  - docs/README-QUICKSTART.md
  - docs/INDICE_DOCUMENTOS.md
- Scripts utilitarios e QA: scripts/
- Scripts auxiliares de backend: backend/scripts/

## Seguranca e Consistencia

- O backend bloqueia startup com configuracao invalida em production.
- Nao usar SQLite em production.
- Nao expor tokens em commits, logs ou docs.
- Tratar arquivos fly.toml e docs com placeholders como templates, nunca como segredos reais.
