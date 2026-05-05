# Production Deployment Guide

Este documento descreve os passos obrigatórios para fazer deploy do Dashboard Analytics em produção (Fly.io, Render ou similar).

---

## CHECKLIST PRÉ-DEPLOY (OBRIGATÓRIO)

### 1. Backend Configuration (fly.toml)

**Adicionar seção `[env]` com variáveis de ambiente:**

```toml
[env]
  DATABASE_URL = "postgresql://user:password@db.internal/dashboard"
  CORS_ORIGINS = "https://dashboard.fly.dev,https://www.dashboard.fly.dev"
  EXTERNAL_SYNC_TOKEN = "gerar-token-aleatorio-seguro-32-chars-aqui"
  EXTERNAL_SYNC_MIN_INTERVAL_SECONDS = "60"
  ENV = "production"
  ALLOW_SEED = "false"
```

**Validar:**
- `DATABASE_URL` aponta para PostgreSQL (NÃO SQLite)
- `CORS_ORIGINS` inclui domínio final
- `EXTERNAL_SYNC_TOKEN` é único e seguro (min 32 caracteres)

### 2. Frontend Configuration (.env.production)

```bash
VITE_API_BASE_URL=https://dashboard.fly.dev/api
VITE_USE_EXTERNAL=true
VITE_EXTERNAL_SYNC_TOKEN=mesmo-token-do-backend-backend
```

**Validar:**
- `VITE_API_BASE_URL` aponta para domínio final
- `VITE_EXTERNAL_SYNC_TOKEN` sincronizado com backend

### 3. Database Setup

**ANTES de fazer deploy:**

```bash
# 1. Criar banco PostgreSQL em produção (e.g., via Fly.io)
# 2. Configurar CONNECTION STRING em DATABASE_URL
# 3. Testar conexão localmente:
PGPASSWORD=senha psql -h host -U user -d dashboard -c "SELECT 1"
```

**Configuração em Fly.io:**

```bash
# Criar volume para PostgreSQL
fly volumes create pg_data --size 10

# Ou adicionar app PostgreSQL separado
fly postgres create
```

### 4. Health Check Endpoints

Backend expõe dois endpoints para monitoring:

- `GET /health` → Liveness probe (HTTP 200)
- `GET /readiness` → Readiness probe (HTTP 200/503)

**Configurar em fly.toml:**

```toml
[checks]
  [checks.http]
    grace_period = "10s"
    interval = "30s"
    method = "get"
    path = "/readiness"
    protocol = "http"
    timeout = "10s"
    type = "http"
```

---

## DEPLOY STEPS

### Step 1: Build Frontend

```bash
pnpm install
pnpm build  # Gera dist/ com VITE_API_BASE_URL baked-in
```

**Validar:**
```bash
ls -la dist/
# Deve ter: index.html, assets/*, config verificado
cat dist/index.html | grep "VITE_API"
```

### Step 2: Deploy Backend

```bash
# Build Docker image
fly deploy

# Logs em tempo real
fly logs -f
```

**Validar:**
```bash
# Testar health check
curl https://dashboard.fly.dev/health
curl https://dashboard.fly.dev/readiness

# Testar endpoint real
curl https://dashboard.fly.dev/api/overview
```

### Step 3: Test Integration

```bash
# Frontend deve carregar
curl https://dashboard.fly.dev/
# Deve ter <script>...</script> com app inicializado
```

---

## Security Checklist

- `EXTERNAL_SYNC_TOKEN` configurado (não vazio)
- `CORS_ORIGINS` não contém `*` (whitelist explícita)
- `DATABASE_URL` usa PostgreSQL (não SQLite ephemeral)
- Logs sem stack trace (logging.error(..., exc_info=False))
- Endpoints internos protegidos por token (`/internal/**`)
- HTTPS forçado (fly.io faz redirect automático)

---

## Troubleshooting

### Frontend recebe CORS error

**Problema:** `Access-Control-Allow-Origin` não match

**Solução:**
```bash
# Verificar CORS_ORIGINS
fly secrets set CORS_ORIGINS="https://seu-dominio.fly.dev"

# Testar preflight
curl -X OPTIONS http://localhost:8000/api/overview \
  -H "Origin: https://seu-dominio.fly.dev" \
  -H "Access-Control-Request-Method: GET"
```

### Frontend conecta mas recebe 500 de API

**Problema:** Backend error ou DB não conecta

**Solução:**
```bash
# Check readiness
curl http://localhost:8000/readiness

# Check logs
fly logs -f | grep ERROR

# Validar DATABASE_URL
fly config view | grep DATABASE_URL
```

### Database connection timeout

**Problema:** Firewall ou network issue

**Solução:**
```bash
# Test connection
fly ssh console
# psql -h db.internal -U postgres -d dashboard -c "SELECT 1"

# Rebuild connection string
DATABASE_URL="postgresql://user:pass@db.internal/dashboard?sslmode=require"
```

---

## Monitoring

### Essential Metrics

1. **Health Check Response Time** (`/readiness`)
   - Target: <500ms
   - Alert if: >2s

2. **API Latency** (`/api/overview`)
   - Target: <100ms
   - Alert if: >500ms

3. **Error Rate** (5xx responses)
   - Target: <0.1%
   - Alert if: >1%

4. **Database Connection Pool**
   - Monitor connections used vs available
   - Alert if: >90% utilized

### Logs to Monitor

```bash
fly logs -f | grep "\[ERROR\]\|\[READINESS\]"
```

---

## Rollback Procedure

Se deploy quebrar:

```bash
# Ver versão anterior
fly releases

# Rollback para versão anterior
fly releases rollback

# Validar
curl https://dashboard.fly.dev/health
```

---

## Post-Deploy Verification

- Health check: `curl https://dashboard.fly.dev/health`  
- Readiness: `curl https://dashboard.fly.dev/readiness`  
- API endpoint: `curl https://dashboard.fly.dev/api/overview`  
- Frontend loads: `curl https://dashboard.fly.dev/ | grep "<div id=\"root\""  
- Logs no errors: `fly logs | grep ERROR`

---

**Last Updated:** 4 de maio de 2026  
**Status:** PRODUCTION READY (com configuração correta)
