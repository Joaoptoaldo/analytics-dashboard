# Dashboard de Analise

Projeto full stack de dashboard analitico com foco em KPIs, filtros reais, graficos e tabela de dados com visual de produto SaaS.

## Stack atual

### Frontend

* React 19
* Vite
* TypeScript
* Tailwind CSS v4
* shadcn/ui
* Radix UI
* Recharts
* SWR

### Backend

* Python
* FastAPI
* Uvicorn

## Estado atual

O repositorio ja possui um MVP funcional com:

* sidebar responsiva
* cards de KPI
* grafico de linha
* grafico de distribuicao
* filtros conectados ao backend
* tabela com busca, ordenacao e paginacao
* seed mock em memoria para demonstracao

O frontend principal esta em `src/` e o backend atual esta concentrado em `backend/main.py`.

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
└── TODO.md
```

## Como rodar

### Frontend

```bash
npm install
npm run dev
```

### Backend

Use o ambiente Python de sua preferencia e rode:

```bash
cd backend
uv run python -m uvicorn main:app --reload
```

Se voce nao usar `uv`, rode o equivalente com `python`/`pip` no seu ambiente.

## Endpoints atuais

* `GET /`
* `GET /api/overview`
* `GET /api/sales`
* `GET /api/traffic`
* `GET /api/products`
* `GET /api/filters`
* `GET /api/activity`
* `GET /api/recent-orders`

## Ponto de atencao

Este projeto ainda esta em transicao entre uma base de MVP e uma arquitetura mais robusta. Hoje existem alguns residuos de estrutura inspirada em Next.js e algumas duplicacoes utilitarias que ainda devem ser limpas.

Considere como verdade operacional:

* frontend em TypeScript com Vite
* backend FastAPI ainda monolitico
* persistencia real ainda nao implementada
* documentacao e arquitetura em processo de alinhamento

## Proximos passos sugeridos

* remover duplicacoes de hooks e utils
* modularizar o backend
* introduzir SQLite/SQLAlchemy
* separar melhor os componentes de dashboard
* reduzir tamanho do bundle frontend
* adicionar autenticacao e navegacao real
