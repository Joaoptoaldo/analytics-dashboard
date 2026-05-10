# Quickstart

## 1) Requisitos

- Node.js 18+
- Python 3.11+
- pnpm

## 2) Instalar dependencias

```bash
pnpm install
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
```

## 3) Variaveis de ambiente (minimo local)

```env
VITE_API_BASE_URL=http://localhost:8080/api
ENV=development
DATABASE_URL=sqlite:///./backend.db
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
ALLOW_SEED=false
EXTERNAL_SYNC_TOKEN=
EXTERNAL_SYNC_MIN_INTERVAL_SECONDS=60
```

## 4) Subir backend

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8080
```

## 5) Subir frontend

```bash
pnpm run dev
```

## 6) Smoke test

```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/readiness
curl http://127.0.0.1:8080/api/overview
```

## 7) Sync interno (opcional)

```bash
curl -X POST http://127.0.0.1:8080/internal/external-products/sync -H "x-internal-token: <token>"
```

Observacao: o endpoint de sincronizacao e interno e exige token valido.
