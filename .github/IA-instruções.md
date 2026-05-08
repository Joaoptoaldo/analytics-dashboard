# Contexto do Projeto

Voce esta me ajudando a construir o **Dashboard de Analise**, um sistema full stack com foco em visualizacao de dados, KPIs, filtros, tabelas e graficos com aparencia de produto SaaS.

O projeto ja possui um MVP funcional, mas o objetivo agora e evoluir a base atual com mais consistencia arquitetural, melhor documentacao, backend mais robusto e experiencia mais proxima de producao.


# Estado Real do Repositorio

## Frontend atual

Stack em uso hoje:

* React 19
* Vite
* TypeScript
* Tailwind CSS v4
* shadcn/ui + Radix UI
* Recharts
* SWR
* Lucide React

Arquivos principais atuais:

* `src/main.tsx`
* `src/App.tsx`
* `src/Dashboard.tsx`
* `hooks/use-dashboard.ts`
* `components/ui/*`
* `app/globals.css`

Observacoes importantes:

* O projeto **nao esta em JavaScript puro**; a base atual usa TypeScript.
* Ha arquivos residuais em `app/` que vieram de uma estrutura inspirada em Next.js, mas o entrypoint real hoje e o Vite em `src/main.tsx`.
* A UI principal atual esta concentrada em `src/App.tsx` e `src/Dashboard.tsx`.
* O CSS global ativo esta sendo importado de `app/globals.css` em `src/main.tsx`.
* Ainda existem duplicacoes utilitarias e arquivos legados que devem ser tratados com cuidado antes de qualquer limpeza estrutural.

## Backend atual

Stack em uso hoje:

* Python
* FastAPI
* Uvicorn
* CORS configurado

Arquivos principais atuais:

* `backend/main.py`
* `backend/pyproject.toml`

Observacoes importantes:

* O backend estava originalmente concentrado em um unico arquivo, mas foi evoluindo: hoje ja existe integracao com `models/`, `services/` e `routers/` e uso de SQLAlchemy para persistencia.
* Produtos externos sao sincronizados da DummyJSON e persistidos atraves do endpoint `POST /api/external-products/sync`.
* A base foi atualizada para que dados apresentados no dashboard venham do banco, nao mais de um dataset em memoria. Ao trabalhar com o backend, preserve compatibilidade com os endpoints existentes.

---

# Direcao Tecnica do Projeto

## O que ja existe

Hoje o projeto ja entrega:

* sidebar responsiva
* dashboard com KPIs
* grafico de linha
* grafico de pizza
* tabela com paginacao
* filtros funcionais conectados ao backend
* ordenacao na tabela
* consumo de API com SWR
* contrato frontend/backend funcional via endpoints FastAPI

## O que ainda e objetivo de evolucao

Evolucoes planejadas (prioritarias):

* consolidar a modularizacao do backend (rotas, services, modelos separados)
* preparar migracao para PostgreSQL a partir de uma camada de acesso bem definida
* separar melhor os componentes de dashboard e reduzir duplicacoes
* adicionar autenticacao e autorizacao
* melhorar performance do bundle frontend
* fortalecer documentacao e testes automatizados

---

# Estrutura Atual do Projeto

```txt
dashboard-de-analise/
|-- .github/
|   `-- IA-instrucoes.md
|-- app/
|   |-- globals.css
|   `-- page.tsx
|-- backend/
|   |-- main.py
|   |-- pyproject.toml
|   `-- uv.lock
|-- components/
|   |-- theme-provider.tsx
|   `-- ui/
|-- hooks/
|   |-- use-dashboard.ts
|   |-- use-mobile.ts
|   `-- use-toast.ts
|-- lib/
|   |-- utils.js
|   `-- utils.ts
|-- public/
|   `-- icon.svg
|-- src/
|   |-- App.tsx
|   |-- Dashboard.tsx
|   `-- main.tsx
|-- index.html
|-- package.json
|-- tsconfig.json
|-- vite.config.ts
`-- README.md
```

---

# Variaveis de Ambiente

Padrao do projeto:

* usar prefixo `VITE_` no `.env` da raiz

Variaveis obrigatorias para setup:

* `VITE_API_BASE_URL`
* `VITE_USE_EXTERNAL`
* `VITE_CORS_ORIGINS`
* `VITE_DATABASE_URL`
* `VITE_ALLOW_SEED`
* `VITE_ENV`
* `VITE_EXTERNAL_SYNC_TOKEN`
* `VITE_EXTERNAL_SYNC_MIN_INTERVAL_SECONDS`
* `VITE_FRONTEND_PORT`
* `VITE_BACKEND_PORT`
* `VITE_USE_MOCKS`
* `VITE_LOG_LEVEL`
* `VITE_ENABLE_ANALYTICS`
* `VITE_ENABLE_ERROR_TRACKING`
* `VITE_ENABLE_PERFORMANCE_MONITORING`
* `VITE_SENTRY_DSN`
* `VITE_SENTRY_ENVIRONMENT`
* `VITE_SENTRY_RELEASE`

---

# Endpoints Relevantes

* `GET /api/products`
* `GET /api/external-products`
* `POST /api/external-products/sync`
* `GET /api/overview`
* `GET /api/sales`
* `GET /api/sales/monthly`
* `GET /api/sales/trend`
* `GET /api/distribution/category`
* `GET /api/top/products`
* `GET /api/metrics/ticket-average`
* `GET /api/activity`
* `GET /api/filters`

---

# Regras de Colaboracao

## Regra principal

Antes de alterar codigo, instalar dependencias, refatorar estrutura ou tomar decisao com impacto arquitetural:

1. explique o que pretende fazer
2. diga por que isso faz sentido no contexto atual do projeto
3. destaque impactos, tradeoffs e arquivos afetados
4. aguarde minha autorizacao explicita

Autorizacoes validas:

* `pode fazer`
* `vai`
* `sim`
* `segue`
* ou equivalente

## Quando eu pedir ajuda

* explique a logica antes do codigo
* conecte a solucao a arquitetura atual do projeto
* diferencie claramente:
  * estado atual
  * divida tecnica
  * direcao futura
* aponte riscos tecnicos e consequencias
* priorize solucoes limpas e sustentaveis
* evite "gambiarra"

## Quando sugerir codigo

* informe quais arquivos serao alterados
* diga se a mudanca e local ou se impacta outras partes
* avise quando houver debito tecnico sendo criado
* se houver mais de um caminho razoavel, apresente as opcoes antes de implementar

## Se eu errar algo

* corrija de forma didatica
* explique a causa raiz
* me ajude a evitar repetir o erro
* mostre como a correcao se encaixa na arquitetura geral

---

# Regras Tecnicas

## Sobre a stack

* considere **TypeScript** como padrao atual do frontend
* nao proponha voltar para JavaScript sem alinhamento explicito
* preserve Vite como bundler atual
* use a arquitetura existente como ponto de partida, nao como se ja fosse a arquitetura final

## Sobre frontend

* preservar o design system baseado em shadcn/ui e Radix
* evitar duplicacao de hooks, utils e estilos
* preferir componentizacao clara quando isso realmente melhorar manutencao
* nao criar paginas falsas so para parecer completo
* filtros devem continuar sendo reais, nao decorativos
* tratar `app/` como residuo de transicao ate que haja decisao explicita de remover ou reaproveitar essa estrutura

## Sobre backend

* manter compatibilidade com o contrato atual consumido pelo frontend
* evitar quebrar endpoints existentes sem avisar antes
* quando propor persistencia adicional, priorizar solucoes que facilitem migracao para bancos gerenciados

## Sobre documentacao

* sempre atualizar docs quando a implementacao mudar de direcao
* nunca descrever como "pronto" algo que ainda e apenas objetivo futuro
* diferenciar claramente visao do produto versus codigo ja implementado
* nao citar arquivos, modulos ou fluxos que nao existam mais no repositorio atual

---

# O que Evitar

* assumir que a arquitetura alvo ja esta pronta
* misturar documentacao aspiracional com documentacao operacional
* criar estruturas grandes sem necessidade imediata
* instalar pacotes sem explicar a justificativa
* refatorar por estetica sem ganho claro
* manter arquivos duplicados por muito tempo
* esconder riscos de manutencao

---

# Commits

Quando sugerir commits, usar Conventional Commits.

Exemplos:

* `feat:`
* `fix:`
* `chore:`
* `refactor:`
* `docs:`
* `test:`

Nunca sugerir commits genericos.

---

# Orientacao de Evolucao

Prioridades gerais do projeto:

1. alinhar documentacao com o codigo real
2. reduzir inconsistencias e duplicacoes
3. modularizar frontend e backend sem refatoracao destrutiva
4. introduzir persistencia real
5. preparar autenticacao e expansao funcional
6. melhorar qualidade de build, performance e deploy

Ao sugerir proximos passos, priorize:

* coerencia arquitetural
* manutencao futura
* clareza para portfolio profissional
* progressao incremental sem quebrar o MVP atual
* comunicacao clara sobre o que e codigo real versus objetivo futuro
* sempre destacar o impacto e tradeoffs de cada mudanca proposta
