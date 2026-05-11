# Checklist de Deploy Prático

**Status:** PRONTO PARA DEPLOY

Stack: Vercel (Frontend) + Render (Backend) + Neon PostgreSQL (Database)

---

## 1. PRÉ-DEPLOY - Validações Locais

### 1.1 Código

```bash
# Frontend
pnpm run lint
# Esperado: 0 errors

pnpm run build
# Esperado: built in X.XXs

# Backend
cd backend
pip audit
# Esperado: sem vulnerabilidades críticas
```

### 1.2 Git

```bash
# Verificar nenhum .env commitado
git status | grep -E "\.env"
# Esperado: nenhuma saída

# Verificar .gitignore
grep "env" .gitignore
# Esperado: *.env, .env.local, etc.
```

### 1.3 Limpar Artifacts

```bash
# Remover DB's de teste
rm -f *.db

# Remover cache
rm -rf .pytest_cache __pycache__ node_modules/.cache

# Remover server.py (foi apenas para teste local)
rm -f server.py
```

### 1.4 Estrutura

- [x] Frontend: src/, components/, lib/, hooks/ presentes
- [x] Backend: backend/main.py, models/, routers/ presentes
- [x] Migrations: alembic/ com versions OK
- [x] Docker: Dockerfile atualizado
- [x] render.yaml: presente

---

## 2. DEPLOY VERCEL (Frontend)

### 2.1 Preparar

```bash
pnpm run build
pnpm run preview   # Testar localmente
```

### 2.2 Conectar

1. https://vercel.com/new
2. Importar GitHub
3. Framework: Vite
4. Build Command: `pnpm run build`
5. Output: `dist`
6. Deploy

### 2.3 Configurar Variáveis

Vercel → Settings → Environment Variables:

```
VITE_API_BASE_URL = https://seu-render-app.onrender.com/api
```

### 2.4 Validar

```bash
curl https://seu-dominio.com/
# Status: 200 OK
```

---

## 3. DEPLOY RENDER (Backend)

### 3.1 Preparar Neon

Acessar https://console.neon.tech:

1. Create New Project
2. Copiar connection string (com pooler)

### 3.2 Conectar

1. https://dashboard.render.com/new/web
2. Conectar GitHub
3. Runtime: Docker
4. Deploy

### 3.3 Configurar Variáveis

Render → Environment:

```
ENV = production
DATABASE_URL = postgresql://...(Neon connection string)
CORS_ORIGINS = https://seu-dominio.com,https://www.seu-dominio.com
ALLOW_SEED = false
EXTERNAL_SYNC_MIN_INTERVAL_SECONDS = 300
```

### 3.4 Health Check

Render → Health Check:

```
Path: /health
Check Interval: 30s
Timeout: 5s
```

### 3.5 Validar

```bash
curl https://seu-render-app.onrender.com/health
# {status: ok}

curl https://seu-render-app.onrender.com/readiness
# {status: ready, database: ok, schema: ok}

curl https://seu-render-app.onrender.com/api/overview
# {total_revenue: X, total_orders: X, ...}
```

---

## 4. PÓS-DEPLOY

- [ ] Frontend carrega
- [ ] Backend responde
- [ ] Dashboard exibe dados
- [ ] Paginação funciona
- [ ] Filtros funcionam
- [ ] Logs sem errors
- [ ] CORS headers presentes
