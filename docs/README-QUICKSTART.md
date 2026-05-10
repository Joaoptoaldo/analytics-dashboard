# Quickstart - Rodando Localmente

## 1) Requisitos

- Node.js 20+
- Python 3.11+
- pnpm (ou npm)

## 2) Instalar dependências

```bash
pnpm install
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r backend/requirements.txt
```

## 3) Variáveis de ambiente (mínimo local)

Criar `.env.local` na raiz:

```env
# Frontend
VITE_API_BASE_URL=http://127.0.0.1:8000/api

# Backend
ENV=development
DATABASE_URL=sqlite:///./backend.db
CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
ALLOW_SEED=false
EXTERNAL_SYNC_MIN_INTERVAL_SECONDS=60
```

## 4) Subir backend

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Backend responde em: http://127.0.0.1:8000

## 5) Subir frontend (em outro terminal)

```bash
pnpm run dev
```

Frontend responde em: http://127.0.0.1:5173

## 6) Validação rápida

```bash
# Backend health
curl http://127.0.0.1:8000/health

# Backend readiness
curl http://127.0.0.1:8000/readiness

# API data
curl http://127.0.0.1:8000/api/overview
```

## 7) Sync interno (opcional)

```bash
curl -X POST http://127.0.0.1:8080/internal/external-products/sync -H "x-internal-token: <token>"
```

Observacao: o endpoint de sincronizacao e interno e exige token valido.
