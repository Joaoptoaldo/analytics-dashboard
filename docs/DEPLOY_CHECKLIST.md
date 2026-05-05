# CHECKLIST DE DEPLOY PRÁTICO

**Status:** 🟢 **PRONTO PARA DEPLOY**

---

## 1. PRÉ-DEPLOY (Executar Antes de Fazer Deploy)

### 1.1 Validar Código
- [x] Backend completo e testado
- [x] Config validation implementada (fail-fast)
- [x] Security headers adicionados
- [x] CORS configurado corretamente
- [x] Health endpoints implementados
- [x] Internal endpoints protegidos com token

### 1.2 Validar Ambiente
```bash
# Verificar que nenhum .env foi committado
git status | grep "\.env"  # Deve estar em .gitignore

# Verificar variáveis de ambiente esperadas
# DATABASE_URL, CORS_ORIGINS, EXTERNAL_SYNC_TOKEN, ENV
```

### 1.3 Limpar Artifacts de Teste
```bash
rm -f backend_qa.db backend_qa_new.db
rm -f qa_report.json qa_production_strictness.json
rm -f seed_qa.py check_db.py
```

---

## 2. DEPLOY PARA FLY.IO

### 2.1 Preparar Variáveis de Ambiente

```bash
# Registrar no Fly CLI
fly auth login

# Criar/actualizar app
fly app list
fly apps create dashboard-de-analise  # Se novo

# Set environment variables
fly secrets set \
  ENV=production \
  DATABASE_URL=postgresql://user:password@host:5432/dashboard_prod \
  CORS_ORIGINS=https://seu-frontend.com,https://www.seu-frontend.com \
  EXTERNAL_SYNC_TOKEN=$(head -c 32 /dev/urandom | base64) \
  ALLOW_SEED=false

# Verificar
fly secrets list
```

### 2.2 Verificar fly.toml

```toml
[app]
primary_region = "gig"  # Seu region preferido

[[services]]
ports = { handlers = ["http"], port = 8080 }
processes = ["app"]

[checks.http]
grace_period = "10s"
interval = "30s"
method = "GET"
path = "/health"
protocol = "http"
timeout = "5s"
type = "http"

[checks.database]
grace_period = "15s"
interval = "30s"
method = "GET"
path = "/readiness"
protocol = "http"
timeout = "10s"
type = "http"
```

### 2.3 Deploy

```bash
# Build e deploy
fly deploy

# Monitorar logs
fly logs

# Testar endpoints
curl https://your-app.fly.dev/health
curl https://your-app.fly.dev/readiness
curl https://your-app.fly.dev/api/products
```

### 2.4 Monitoramento Pós-Deploy (Fly.io)

```bash
# Ver status
fly status

# Ver logs
fly logs --follow

# Se houver erro:
# 1. Verificar logs: fly logs
# 2. Verificar secrets: fly secrets list
# 3. Rollback se necessário: fly builds list && fly deploy <BUILD_ID>
```

---

## 3. DEPLOY PARA RENDER

### 3.1 Preparar no Painel Render

1. **Conectar GitHub:**
   - Go to render.com/dashboard
   - Connect GitHub account
   - Select repository

2. **Criar New Service:**
   - Type: Web Service
   - Name: dashboard-de-analise
   - Runtime: Docker
   - Build Command: `(deixar vazio - usa Dockerfile)`
   - Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}`

3. **Environment Variables:**
   ```
   ENV=production
   DATABASE_URL=postgresql://user:password@host:5432/dashboard_prod
   CORS_ORIGINS=https://seu-frontend.com
   EXTERNAL_SYNC_TOKEN=<gerar token 32+ chars>
   ALLOW_SEED=false
   PORT=10000
   ```

4. **Health Check:**
   - Path: `/readiness`
   - Check Interval: 30s
   - Timeout: 10s
   - Failure Threshold: 3

5. **Deploy:**
   - Click "Deploy" button
   - Monitorar logs em tempo real

### 3.2 Verificar Deploy Render

```bash
# Testar após deployment
curl https://seu-app.onrender.com/health
curl https://seu-app.onrender.com/readiness
curl https://seu-app.onrender.com/api/products

# Se erro, verificar:
# 1. Render Logs tab
# 2. Environment variables in Settings
# 3. Build logs
```

---

## 4. PÓS-DEPLOY (Ambas Plataformas)

### 4.1 Testes Funcionais (24 horas)

```bash
# Em a forma: substituir YOUR_DOMAIN

# 1. Health check
curl -i https://YOUR_DOMAIN/health
# Esperado: 200 OK

# 2. Readiness check
curl -i https://YOUR_DOMAIN/readiness
# Esperado: 200 OK

# 3. Test CORS
curl -H "Origin: https://seu-frontend.com" \
  -H "Access-Control-Request-Method: GET" \
  -X OPTIONS https://YOUR_DOMAIN/api/products \
  -v
# Esperado: Access-Control-Allow-Origin header present

# 4. List products
curl https://YOUR_DOMAIN/api/products | jq '.items | length'
# Esperado: número > 0

# 5. Test internal endpoint (deve falhar sem token)
curl -X POST https://YOUR_DOMAIN/internal/external-products/sync \
  -H "x-internal-token: wrong"
# Esperado: 401 Unauthorized
```

### 4.2 Monitoramento 24/7

**Ativar em ambas plataformas:**

- [ ] Health check endpoint: `/health`
- [ ] Readiness check: `/readiness`
- [ ] Alert se status != 200
- [ ] Alert se response time > 5s
- [ ] Alert se CPU > 80%
- [ ] Alert se Memory > 80%

### 4.3 Logs & Alertas

- Verificar logs diariamente primeira semana
- Look for:
  - `ConfigError` messages (nunca deve aparecer em PROD)
  - `[ERROR]` or `[CRITICAL]` messages
  - Unusual slowdowns
  - Database connection issues

### 4.4 Backup & Recovery Plan

1. **Backup Database:**
   ```bash
   # Fly.io com Postgres addon
   fly postgres backup list -a DATABASE_APP_NAME
   
   # Render Postgres
   # Configurar auto-backups no painel Render
   ```

2. **Recovery Procedure:**
   ```
   1. Get latest backup ID
   2. Restore from backup (via CLI or web)
   3. Verify /readiness returns 200
   4. Test APIs manually
   ```

---

## 5. TROUBLESHOOTING RÁPIDO

| Problema | Solução |
|----------|---------|
| `ConfigError` no startup | Verificar ENV vars: `ENV`, `DATABASE_URL`, `CORS_ORIGINS`, `EXTERNAL_SYNC_TOKEN` |
| `/readiness` retorna 503 | Database não conectando. Verificar `DATABASE_URL` e credenciais |
| CORS error no frontend | Verificar `CORS_ORIGINS` matches frontend URL exatamente |
| 500 Internal Server Error | Verificar logs: `fly logs` ou Render logs tab |
| Apps crashes immediately | Verificar `ALLOW_SEED=false` em PROD |
| Sync endpoint 401 | Verificar `EXTERNAL_SYNC_TOKEN` matches em frontend |

---

## 6. ROLLBACK PROCEDURE

**Se problemas críticos após deploy:**

### Fly.io Rollback
```bash
# Ver histórico de builds
fly builds list

# Rollback para build anterior
fly deploy <BUILD_ID>

# Ou:
fly releases list
fly releases rollback
```

### Render Rollback
```
1. Go to Deployments tab
2. Click "Deploy" next to previous successful deployment
3. Confirm
```

**Estimated rollback time:** < 5 minutos

---

## 7. CHECKLIST FINAL PRÉ-DEPLOY

- [ ] Todos os 26 QA tests passaram
- [ ] Database URL é PostgreSQL (não SQLite)
- [ ] EXTERNAL_SYNC_TOKEN gerado e seguro (32+ chars)
- [ ] CORS_ORIGINS configurado para domínio real
- [ ] ENV=production em ambas plataformas
- [ ] ALLOW_SEED=false
- [ ] Docker builds sem erros
- [ ] Health endpoints testados localmente
- [ ] fly.toml ou render.yaml atualizados
- [ ] Backup database antes de deploy
- [ ] Time informado sobre deployment
- [ ] Monitoring alerts configurados

---

## 8. CONTATOS & DOCUMENTAÇÃO

**Documentação:**
- [QA_FINAL_REPORT.md](QA_FINAL_REPORT.md) - Relatório completo
- [QA_AUDIT_CONSOLIDADO.json](QA_AUDIT_CONSOLIDADO.json) - Dados estruturados
- [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) - Deploy guide

**Scripts Úteis:**
- `qa_test_fullstack.py` - Rodar testes QA
- `qa_test_production_validation.py` - Testar strictness

---

## 9. SIGN-OFF

| Role | Name | Date | Approval |
|------|------|------|----------|
| QA Lead + SRE | Agent | 2026-05-05 | ✅ APPROVED |
| Backend Dev | (You) | _ | _ |
| DevOps/Infra | (You) | _ | _ |

---

**DEPLOYMENT WINDOW:** 🟢 OPEN

**NEXT REVIEW:** 24h post-deployment (monitoring check-in)

**SUPPORT:** If issues arise, refer to [QA_FINAL_REPORT.md](QA_FINAL_REPORT.md) troubleshooting section or contact DevOps team.
