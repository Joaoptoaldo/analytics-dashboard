# Próximos Passos de Deploy

**Sistema aprovado para produção.** Arquitetura: Vercel (frontend) + Render (backend) + Neon (database)

---

## Arquitetura

```
Vercel (SPA)          Render (API)        Neon (PostgreSQL)
https://seu-dominio → https://seu-app.onrender.com → pooler
```

---

## 1. Frontend - Vercel

### Preparar

```bash
pnpm run build      # Gera dist/
ls -la dist/        # Verificar tamanho < 2MB
```

### Deploy

1. Ir para https://vercel.com/new
2. Conectar seu repositório GitHub
3. Framework: Vite
4. Build: `pnpm run build`
5. Output: `dist`

### Variáveis (Vercel → Settings → Environment Variables)

```
VITE_API_BASE_URL = https://seu-render-app.onrender.com/api
```

### Validar

```bash
curl https://seu-dominio.com/
# Status: 200, HTML da SPA

curl https://seu-dominio.com/assets/index-*.js | head -c 100
# Contém: http://... (URL da API compilada)
```

---

## 2. Backend - Render

### Preparar Neon

1. Acessar https://console.neon.tech
2. Criar novo projeto PostgreSQL
3. Copiar connection string (com pooler)

### Deploy

1. Ir para https://dashboard.render.com/new/web
2. Conectar GitHub
3. Runtime: Docker
4. Build Command: (vazio - usa Dockerfile)
5. Start Command: (vazio - usa Dockerfile CMD)

### Variáveis (Render → Environment)

```
ENV = production
DATABASE_URL = postgresql://...(Neon connection string)
CORS_ORIGINS = https://seu-dominio.com,https://www.seu-dominio.com
ALLOW_SEED = false
EXTERNAL_SYNC_MIN_INTERVAL_SECONDS = 300
```

### Health Check (Render → Health Check)

```
Path: /health
Interval: 30s
Timeout: 5s
```

### Validar

```bash
# Health
curl https://seu-render-app.onrender.com/health
# {status: ok}

# Readiness
curl https://seu-render-app.onrender.com/readiness
# {status: ready, database: ok, schema: ok}

# Data
curl https://seu-render-app.onrender.com/api/overview
# {total_revenue: X, total_orders: X, ...}
```

---

## 3. Validação End-to-End

```bash
# 1. Frontend carrega
curl https://seu-dominio.com/ | head -c 200

# 2. Abrir em navegador e verificar:
# - Dashboard exibe dados ✓
# - Network shows /api/* requests ✓
# - CORS headers presentes ✓

# 3. Testar funcionalidades:
# - Clique em "Próxima" (paginação)
# - Selecione filtro de categoria
# - Verifique gráficos
```

---

## 🚨 Troubleshooting

| Problema | Causa | Solução |
|----------|-------|---------|
| 404 em /api/* | VITE_API_BASE_URL não configurada | Adicionar em Vercel env |
| CORS error | CORS_ORIGINS incorreta | Adicionar domínio Vercel em Render |
| Database error | DATABASE_URL inválida | Copiar de Neon (com pooler) |
| Latência > 5s | Neon cold start | Normal, retenta automaticamente |

---

## Checklist Final

- [ ] Frontend: Deploy bem-sucedido em Vercel
- [ ] Backend: Deploy bem-sucedido em Render
- [ ] Database: Conectado via Neon pooler
- [ ] CORS: Funcionando entre Vercel ↔ Render
- [ ] Dashboard: Exibe dados reais
- [ ] Health checks: Passam
- [ ] Logs: Sem errors
- [ ] Funcionalidades: Paginação + Filtros OK
