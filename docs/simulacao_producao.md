# Simulacao de Producao - PostgreSQL + Render + Vercel

Data: 2026-05-08

## Escopo Executado

- Etapa 1: auditoria de producao (codigo e configuracao)
- Etapa 2: preparo backend para Render (ajustes minimos e seguros)
- Etapa 3: preparo frontend para Vercel (ajustes minimos e seguros)
- Etapa 4: simulacao operacional com backend local + PostgreSQL real
- Etapa 5: carga leve controlada

## Evidencias Objetivas

- lint frontend: OK
- build frontend: OK
- pytest relevante backend: 3 passed
- startup backend local: OK
- readiness oscilando com latencia real de PostgreSQL (503 por db_slow seguido de 200)
- endpoint legado /api/sales em PostgreSQL: corrigido e validado em runtime (200)
- /metrics: endpoint responde sem crash (modo degradado quando prometheus_client ausente no ambiente)

## Etapa 1 - Auditoria (curta)

### Bloqueadores encontrados

1. SQL legado com strftime em endpoint de vendas quebrava em PostgreSQL.
2. TypeScript de Sentry com tipagem/env incompleta quebrava build.
3. Fallback SPA para Vercel nao estava explicito (risco de 404 em refresh de rota).

### Riscos reais

1. Readiness pode flapar com Neon por threshold agressivo (300ms).
2. /metrics pode ficar degradado sem prometheus_client no runtime.
3. Endpoint interno de sync retorna 500 quando EXTERNAL_SYNC_TOKEN nao esta configurado (comportamento fail-closed).

### Ajustes obrigatorios aplicados

1. Compatibilidade Postgres/SQLite no agrupamento mensal de /api/sales.
2. Robustez de normalizacao de data no sync externo.
3. Tipagem segura de Sentry e ImportMetaEnv para build.
4. vercel.json com rewrite SPA e cache para assets.
5. Defaults operacionais de pool/timeouts no render.yaml.
6. Timeouts defensivos do gunicorn no Dockerfile.

### Ajustes opcionais pendentes

1. Ajustar threshold de readiness para reduzir falso negativo em rede com latencia variavel.
2. Garantir prometheus_client no ambiente final de deploy.
3. Separar endpoint interno de sync da UI publica (botao/fluxo dedicado de operacao).

## Etapa 2 - Backend Render

Status: pronto para deploy de simulacao (nao definitivo), com:

- PORT dinamico
- gunicorn + uvicorn worker
- healthcheck configurado
- fail-fast de config
- CORS production-safe via validacao
- pool e timeouts de DB parametrizados
- logs estruturados em stdout

## Etapa 3 - Frontend Vercel

Status: pronto para deploy de simulacao (nao definitivo), com:

- build de producao validado
- tipagem de VITE_* ajustada
- fallback SPA (rewrite)
- cache de assets imutaveis
- sem hardcode novo de localhost em producao

## Etapa 4 - Simulacao Operacional

### Resultado

- Script fullstack: 23/24 passed
- Falha observada: endpoint interno protegido retornando 500 quando token ausente no ambiente local (esperado em modo fail-closed para misconfiguration).
- Readiness oscilou entre 503 (db_slow) e 200, com logs estruturados indicando duracao/trace.

## Etapa 5 - Carga Leve

- 20 requests concorrentes leves sem 500 no ciclo de teste
- Sem indicio de vazamento de conexao no ciclo executado
- Gargalo principal observado: latencia intermitente de readiness para Neon

## Proximos Passos para Cloud Real (Render + Vercel)

1. Provisionar servico Render com secrets reais (ENV, DATABASE_URL Neon, CORS_ORIGINS, EXTERNAL_SYNC_TOKEN).
2. Provisionar projeto Vercel com VITE_API_BASE_URL=https://<render-domain>/api.
3. Executar script de validacao apontando para URLs publicas e coletar logs reais de provider.
4. Revalidar CORS com dominio final do Vercel.
5. Ajustar thresholds de readiness conforme latencia observada em producao.

## Simulacao local alinhada

- Frontend preview: `http://127.0.0.1:4175`
- Backend production-like: `http://127.0.0.1:8080`
- Backend usa Neon com `sslmode=require`
- Frontend local usa proxy `/api` no preview
