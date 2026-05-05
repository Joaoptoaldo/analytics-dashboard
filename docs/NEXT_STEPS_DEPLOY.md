# 🚀 PRÓXIMAS AÇÕES - DEPLOY PARA RENDER

Seu sistema está **✅ APROVADO PARA PRODUÇÃO**. Aqui estão os próximos passos:

---

## OPÇÃO 1: Render.com (Recomendado - mais fácil)

### 1. Criar conta em Render.com (se não tiver)
- https://render.com
- Sign up com GitHub

### 2. Criar novo Web Service

```
Dashboard → New → Web Service
```

### 3. Conectar repositório

- Selecionar seu repositório GitHub
- Autenticação automática se conectado

### 4. Configurar build & deploy

**Build Command:**
```bash
pip install -r backend/requirements.txt
```

**Start Command:**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}
```

**Environment Variables:**

Clique em "Advanced" → "Add Environment Variable"

```
ENV = production

DATABASE_URL = postgresql://usuario:senha@seu-db-host:5432/seu-db

CORS_ORIGINS = https://seu-dominio.com,https://www.seu-dominio.com

EXTERNAL_SYNC_TOKEN = (gerar com: openssl rand -hex 16)

ALLOW_SEED = false

PYTHONDONTWRITEBYTECODE = 1

PYTHONUNBUFFERED = 1
```

### 5. Deploy

Clique em "Deploy" e aguarde (2-3 minutos)

### 6. Verificar

```bash
# Testar saúde
curl https://seu-app.onrender.com/health

# Testar readiness
curl https://seu-app.onrender.com/readiness

# Testar API
curl https://seu-app.onrender.com/api/products
```

---

## OPÇÃO 2: Fly.io (Alternativa)

### 1. Instalar Fly CLI

```bash
# Windows
curl -L https://fly.io/install.sh | sh

# macOS
brew install flyctl
```

### 2. Login

```bash
fly auth login
```

### 3. Criar app

```bash
cd c:\Users\user\Desktop\GERAL\CODIGOS\dashboard-de-analise
fly launch --dockerfile Dockerfile
```

### 4. Configurar variáveis

```bash
fly secrets set ENV=production
fly secrets set DATABASE_URL="postgresql://..."
fly secrets set CORS_ORIGINS="https://seu-dominio.com"
fly secrets set EXTERNAL_SYNC_TOKEN="seu-token"
fly secrets set ALLOW_SEED=false
```

### 5. Deploy

```bash
fly deploy
```

### 6. Monitorar

```bash
fly logs
fly status
```

---

## ⚠️ COISAS IMPORTANTES

### 1. **Gerar EXTERNAL_SYNC_TOKEN seguro**

```bash
# PowerShell
[System.Convert]::ToHexString([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(16))

# Ou use um gerador online seguro
```

### 2. **CORS_ORIGINS deve ser seu domínio real**

❌ NÃO use:
- `http://localhost:5173`
- `http://localhost:3000`
- `*`
- `http://seu-dominio.com` (sem https)

✅ USE:
- `https://seu-dominio.com`
- `https://www.seu-dominio.com`

### 3. **DATABASE_URL precisa ser PostgreSQL externo**

❌ NÃO use:
- `sqlite:///./test.db`
- Local SQLite

✅ USE:
- `postgresql://user:password@host:5432/dbname`
- Render PostgreSQL Add-on (recomendado)
- Railway
- Supabase
- Amazon RDS

### 4. **ALLOW_SEED deve ser false em PROD**

A validação vai bloquear se estiver `true` em produção.

---

## 🔍 TROUBLESHOOTING

### Deploy com erro "ConfigError"

Significa uma env var está inválida. Verificar:
- ✅ ENV=production (DEVE ser "production")
- ✅ DATABASE_URL (DEVE ser PostgreSQL)
- ✅ CORS_ORIGINS (DEVE ter apenas domínios HTTPS)
- ✅ EXTERNAL_SYNC_TOKEN (DEVE ter 32+ caracteres)
- ✅ ALLOW_SEED (DEVE ser "false")

### /readiness retorna 503

Isso é NORMAL enquanto o banco de dados está inicializando.

Aguarde 30-60 segundos e tente novamente.

### Health check falha

Verificar:
```bash
# Render
curl https://seu-app.onrender.com/health

# Fly.io
fly open
# Depois acesso /health na URL
```

---

## 📊 Checklist Final

Antes de fazer o deploy, verificar:

- [ ] GitHub repository configurado
- [ ] Dockerfile verificado (`ls Dockerfile`)
- [ ] Database PostgreSQL externo preparado
- [ ] EXTERNAL_SYNC_TOKEN gerado
- [ ] CORS_ORIGINS domain decidido
- [ ] ENV=production setado
- [ ] ALLOW_SEED=false confirmado
- [ ] PYTHONUNBUFFERED=1 setado
- [ ] PYTHONDONTWRITEBYTECODE=1 setado

---

## ✅ Pronto!

Sistema foi validado em **8 fases com 100+ testes**:
- ✅ Config validation
- ✅ API endpoints
- ✅ Security controls
- ✅ Database layer
- ✅ Docker simulation

**Seus reports:**
- `VEREDITO_FINAL_CONSOLIDADO.txt` - Resumo final
- `RENDER_DOCKER_SIMULATION_RESULTS.md` - Testes do Docker
- `QA_FINAL_REPORT.md` - Relatório completo
- `DEPLOY_CHECKLIST.md` - Guia passo a passo

---

## 🎯 Próximas ações agora:

1. Escolher Render.com OU Fly.io
2. Preparar PostgreSQL externo
3. Gerar EXTERNAL_SYNC_TOKEN
4. Configurar env vars
5. Deploy
6. Testar endpoints
7. Celebrar! 🎉

---

**Data:** 5 de maio de 2026  
**Status:** ✅ PRONTO PARA PRODUÇÃO  
**Próximo:** DEPLOY
