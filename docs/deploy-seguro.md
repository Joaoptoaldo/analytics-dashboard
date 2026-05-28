# Deploy Seguro - Checklist de Segurança

## Pré-requisitos

- Python 3.13.13 e Node 20
- Segredos definidos NO PROVEDOR (nunca em arquivo)
- PostgreSQL (Neon) acessível
- Git limpo (sem credenciais)

## Validação local

```bash
# Frontend
pnpm run lint          # 0 errors
pnpm run build         # Sem warnings críticos

# Simulação production-like local
pnpm run preview --host 127.0.0.1 --port 4175

# Backend
pip audit             # Sem vulnerabilidades críticas
DATABASE_URL=sqlite:///./backend.db ENV=development python -c "from backend.main import app; print('OK')"
```

## Variáveis de Ambiente

### Frontend (Vercel)

```
VITE_API_BASE_URL = https://seu-render-app.onrender.com/api
```

Para preview local com proxy, `VITE_API_BASE_URL` pode ser `/api`.

### Backend (Render)

```
ENV = production
DATABASE_URL = (Neon connection string)
CORS_ORIGINS = https://seu-dominio.com,https://www.seu-dominio.com
ALLOW_SEED = false
EXTERNAL_SYNC_MIN_INTERVAL_SECONDS = 300
```

Na simulação local production-like, o backend roda em `127.0.0.1:8080` e o frontend em `127.0.0.1:4175`.

## Checklist de Segurança

**Código:**
- [ ] Nenhum .env commitado (.gitignore contém `.env*`)
- [ ] Nenhuma credencial em logs
- [ ] ESLint: 0 errors
- [ ] pip audit: sem vulnerabilidades críticas

**Configuração:**
- [ ] DATABASE_URL aponta para Neon (nunca SQLite em prod)
- [ ] CORS_ORIGINS limitado aos domínios permitidos
- [ ] ALLOW_SEED = false
- [ ] Nenhum token VITE_* compilado no bundle

**Pós-Deploy:**
- [ ] `GET /health` retorna 200 OK
- [ ] `GET /readiness` retorna 200 OK
- [ ] `GET /api/overview` com CORS headers ✓
- [ ] `GET /api/overview` com CORS headers presente
- [ ] Latência < 1s para overview
- [ ] Logs sem credenciais

## Monitoramento

- Render: Health Checks (/health a cada 30s)
- Vercel: Analytics ativar
- Verificar logs diariamente na primeira semana