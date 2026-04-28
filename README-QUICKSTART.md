# Dashboard de Análise – Instruções 

## Requisitos

- Node.js 18+ (frontend)
- Python 3.11+ (backend)
- pnpm (ou npm/yarn)

## 1. Clonando o projeto

```bash
git clone <repo-url>
cd dashboard-de-analise
```

## 2. Configurando variáveis de ambiente

Crie um arquivo `.env` na raiz (já existe um exemplo):

```
VITE_API_BASE_URL=http://localhost:8000/api
API_BASE_URL=http://localhost:8000/api
CORS_ORIGINS=http://localhost:5173
VITE_USE_EXTERNAL=true
```

- `VITE_API_BASE_URL`: URL base da API para o frontend
- `API_BASE_URL`: URL base da API para o backend
- `CORS_ORIGINS`: Origem permitida para CORS (ajuste conforme porta do frontend)
- `VITE_USE_EXTERNAL`: `true` para usar dados reais da FakeStoreAPI

## 3. Instalando dependências

### Frontend

```bash
pnpm install # ou npm install
```

### Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt  # ou use pyproject.toml com pip >=23.1
```

## 4. Rodando o projeto

### Backend (FastAPI)

```bash
cd backend
uvicorn main:app --reload
```

A API estará em http://localhost:8000/api

### Frontend (Vite)

```bash
pnpm run dev
```

Acesse http://localhost:5173 (ou porta sugerida pelo Vite)

## 5. Fluxo de dados reais

- Clique em "Sincronizar API externa" no Dashboard para importar produtos reais da FakeStoreAPI.
- Os dados são persistidos em SQLite e exibidos na tabela.
- O botão mostra feedback visual de carregando, sucesso ou erro.

## 6. Principais Endpoints

- `GET /api/products` – Produtos internos
- `GET /api/external-products` – Produtos externos (FakeStoreAPI)
- `POST /api/external-products/sync` – Sincroniza e persiste produtos reais

## 7. Observações

- O backend já está modularizado (routers, services, models, schemas)
- O frontend usa SWR para cache e hooks customizados
- O projeto está em evolução: consulte o README principal para detalhes de arquitetura

---

Dúvidas? Veja o README.md principal ou abra uma issue.
