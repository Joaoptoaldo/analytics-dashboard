
# Dashboard de Análise

Dashboard full stack para análise de KPIs, filtros dinâmicos, gráficos e tabela de dados, com visual de produto SaaS e dados reais integrados.


## Stack

### Frontend
- React 19
- Vite + TypeScript
- Tailwind CSS v4
- shadcn/ui, Radix UI
- Recharts
- SWR

### Backend
- Python 3.11+
- FastAPI
- Uvicorn
- SQLAlchemy + SQLite


## Funcionalidades

- Sidebar responsiva
- Cards de KPI
- Gráficos (linha, pizza)
- Filtros dinâmicos conectados ao backend
- Tabela com busca, ordenação e paginação
- Integração com FakeStoreAPI para dados reais de produtos
- Persistência dos produtos externos em SQLite
- Botão de sincronização com feedback visual (loading, sucesso, erro)

O frontend está em `src/` e o backend modularizado em `backend/`.


## Estrutura principal

```txt
.
├── .github/IA-instruções.md
├── app/
├── backend/
├── components/
├── hooks/
├── lib/
├── public/
├── src/
├── styles/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```


## Como rodar localmente

### 1. Requisitos
- Node.js 18+
- Python 3.11+
- pnpm (ou npm/yarn)

### 2. Variáveis de ambiente
Crie um arquivo `.env` na raiz:

```
VITE_API_BASE_URL=http://localhost:8000/api
API_BASE_URL=http://localhost:8000/api
CORS_ORIGINS=http://localhost:5173
VITE_USE_EXTERNAL=true
```

### 3. Instalando dependências

#### Frontend
```bash
pnpm install # ou npm install
```

#### Backend
```bash
cd backend
python -m venv .venv
.venv/Scripts/activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt  # ou use pyproject.toml
```

### 4. Executando

#### Backend (FastAPI)
```bash
cd backend
uvicorn main:app --reload
```
A API estará em http://localhost:8000/api

#### Frontend (Vite)
```bash
pnpm run dev
```
Acesse http://localhost:5173 (ou porta sugerida pelo Vite)


## Principais Endpoints

- `GET /api/products` – Produtos internos
- `GET /api/external-products` – Produtos externos (FakeStoreAPI, persistidos)
- `POST /api/external-products/sync` – Sincroniza e persiste produtos reais
- `GET /api/overview`, `/api/sales`, `/api/traffic`, `/api/filters` – Dados para dashboards


## Fluxo de dados reais

1. Acesse o Dashboard.
2. Clique em "Sincronizar API externa" para importar produtos reais da FakeStoreAPI.
3. Os dados são persistidos em SQLite e exibidos na tabela.
4. O botão mostra feedback visual de carregando, sucesso ou erro.

## Observações

- Backend modularizado (routers, services, models, schemas)
- Frontend usa SWR para cache e hooks customizados
- Projeto em evolução: consulte este README e o README-QUICKSTART.md para detalhes

---

Dúvidas? Veja o README-QUICKSTART.md ou abra uma issue.

## Proximos passos sugeridos

* remover duplicacoes de hooks e utils
* modularizar o backend
* introduzir SQLite/SQLAlchemy
* separar melhor os componentes de dashboard
* reduzir tamanho do bundle frontend
* adicionar autenticacao e navegacao real
