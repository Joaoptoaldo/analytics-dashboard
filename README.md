# Dashboard de Analise

Dashboard full stack para analise de KPIs, filtros dinamicos, graficos e tabela de dados, com visual de produto SaaS e dados reais integrados.

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
- SQLAlchemy (SQLite por padrao; PostgreSQL via `DATABASE_URL`)

## Funcionalidades

- Sidebar responsiva
- Cards de KPI
- Graficos (linha, pizza)
- Filtros dinamicos conectados ao backend
- Tabela com busca, ordenacao e paginacao
- Integracao com DummyJSON para dados reais de produtos
- Persistencia dos produtos externos em banco de dados
- Botao de sincronizacao com feedback visual (loading, sucesso, erro)

O frontend esta em `src/` e o backend modularizado em `backend/`.

## Estrutura principal

```txt
.
|-- .github/IA-instrucoes.md
|-- app/
|-- backend/
|-- components/
|-- hooks/
|-- lib/
|-- public/
|-- src/
|-- index.html
|-- package.json
|-- tsconfig.json
|-- vite.config.ts
`-- README.md
```

## Como rodar localmente

### 1. Requisitos
- Node.js 18+
- Python 3.11+
- pnpm (ou npm/yarn)

### 2. Variaveis de ambiente
Crie um arquivo `.env` na raiz usando o arquivo [.env.example](.env.example) como base.

```env
# === Frontend (Vite - prefixo VITE_) ===
VITE_API_BASE_URL=http://localhost:8000/api
VITE_USE_EXTERNAL=true
# Token opcional para sincronização (deve corresponder a EXTERNAL_SYNC_TOKEN do backend)
VITE_EXTERNAL_SYNC_TOKEN=

# === Backend (FastAPI - sem prefixo) ===
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DATABASE_URL=sqlite:///./backend.db
ENV=development
ALLOW_SEED=false
# Segurança da sincronização externa
EXTERNAL_SYNC_TOKEN=
EXTERNAL_SYNC_MIN_INTERVAL_SECONDS=60
```

**Variaveis obrigatorias:**
- Frontend: `VITE_API_BASE_URL` (ex: `https://api.example.com/api` em produção)
- Backend: `DATABASE_URL`, `CORS_ORIGINS`, `ENV`, `ALLOW_SEED`
- Sync externo: `EXTERNAL_SYNC_TOKEN` (frontend e backend devem ter o mesmo valor)
- Rate limit: `EXTERNAL_SYNC_MIN_INTERVAL_SECONDS` (padrão: 60 segundos)

### 3. Instalando dependencias

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
# Se o projeto tiver um pyproject.toml correto, o comando abaixo instala em modo editable:
pip install -e . || pip install -r requirements.txt
```

### 4. Executando

#### Backend (FastAPI)
```bash
uvicorn backend.main:app --reload
```
A API estara em `http://localhost:8000`.

#### Frontend (Vite)
```bash
pnpm run dev
```
Acesse `http://localhost:5173` (ou porta sugerida pelo Vite).

### 5. Comandos uteis para dados reais

- Fazer backup do banco local antes de alteracoes:
```powershell
copy .\backend.db .\backend.db.bak
```
- Limpar a tabela `products` (opcional):
```powershell
sqlite3 backend.db "DELETE FROM products;"
sqlite3 backend.db "VACUUM;"
```
- Sincronizar produtos externos (popula banco):
```powershell
# Rota movida para uso interno (server-only). Se você configurar `EXTERNAL_SYNC_TOKEN`, a chamada
# exige o header `x-internal-token: <token>` e não deve ser exposta a clientes públicos.
curl -X POST http://127.0.0.1:8000/internal/external-products/sync -H "x-internal-token: $EXTERNAL_SYNC_TOKEN"
```
- Verificar contagem e soma de receita no DB:
```powershell
sqlite3 backend.db "SELECT COUNT(*), ROUND(SUM(revenue),2) FROM products;"
```
- Checar endpoint de vendas:
```powershell
curl http://127.0.0.1:8000/api/sales
```

> Observacao: a sincronizacao usa DummyJSON como fonte externa e persiste os dados no banco.

## Principais Endpoints

## Deployment em Produção

### Backend (FastAPI + Gunicorn)

```bash
# Gerar requirements.txt (caso ainda não exista)
cd backend
pip freeze > requirements.txt

# Instalar dependências em produção
pip install -r requirements.txt

# Executar com gunicorn (4 workers, recomendado)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app --bind 0.0.0.0:8000
```

### Frontend (Vite + Build)

```bash
# Build para produção
pnpm run build

# Servir a pasta dist/ com um servidor estático (ex: nginx, Vercel, etc.)
# Ou usar 'vite preview' para teste local
pnpm run preview
```

### Variáveis de Ambiente em Produção

Certifique-se de definir:
- `VITE_API_BASE_URL` → URL da API em produção (ex: `https://api.example.com`)
- `DATABASE_URL` → Connection string PostgreSQL (ex: `postgresql://user:pass@host/dbname`)
- `CORS_ORIGINS` → Domínios permitidos para CORS
- `ENV=production` → Desabilita seed automático

> **Importante:** Nunca exponha credenciais. Use secrets management da sua plataforma (Railway, Heroku, AWS, etc.).

## Principais Endpoints

- `GET /api/products` - Produtos internos
- `GET /api/external-products` - Produtos sincronizados da DummyJSON (persistidos)
- `POST /api/external-products/sync` - Sincroniza e persiste produtos reais
- `GET /api/overview` - KPIs principais
- `GET /api/sales` - Serie de vendas (legado, compatibilidade)
- `GET /api/sales/monthly` - Vendas mensais
- `GET /api/sales/trend?range=30d|90d|180d|1y` - Tendencia de vendas
- `GET /api/distribution/category` - Distribuicao por categoria
- `GET /api/top/products` - Top produtos por receita
- `GET /api/metrics/ticket-average` - Ticket medio mensal
- `GET /api/activity` - Atividade por hora
- `GET /api/filters` - Opcoes de filtros

## Fluxo de dados reais

1. Acesse o Dashboard.
2. Clique em "Sincronizar API externa" para importar produtos reais da DummyJSON.
3. Os dados sao persistidos no banco e exibidos na tabela.
4. O botao mostra feedback visual de carregando, sucesso ou erro.

## Observacoes

- Backend modularizado (routers, services, models, schemas)
- Frontend usa SWR para cache e hooks customizados
- Projeto em evolucao: consulte este README e o README-QUICKSTART.md para detalhes

---

Duvidas? Veja o README-QUICKSTART.md ou abra uma issue.

## Proximos passos sugeridos

- remover duplicacoes de hooks e utils
- separar melhor os componentes de dashboard
- reduzir tamanho do bundle frontend
- adicionar autenticacao e navegacao real

## Testes Automatizados

### Frontend (React)
- Utiliza Jest + Testing Library para testes unitarios e de componentes.
- Scripts disponiveis:
  - `npm run test` - executa todos os testes.
  - `npm run test:watch` - executa testes em modo observacao.
- Exemplo de teste: veja `components/ui/ErrorMessage.test.tsx`.

### Backend (FastAPI)
- Recomenda-se usar `pytest` e `httpx` para testes de API.
- Estrutura sugerida:
  - Crie uma pasta `backend/tests/`.
  - Exemplo de teste para endpoint:

```python
# backend/tests/test_products.py
from fastapi.testclient import TestClient
from backend.main import app


def test_get_products():
    client = TestClient(app)
    response = client.get("/api/products")
    assert response.status_code == 200
    assert "items" in response.json()
```

- Para rodar:
```bash
cd backend
pytest
```

## Variaveis de ambiente
Veja `.env.example` para todas as variaveis necessarias. Sempre mantenha seu `.env` atualizado e nunca faca commit dele.
