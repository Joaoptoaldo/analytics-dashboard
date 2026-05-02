# Deploy Seguro

## Pré-requisitos

- Ambiente com Python 3.11 e Node 20
- Segredos definidos no provedor (não em arquivo versionado)
- Banco de dados acessível para a aplicação

## Variáveis obrigatórias

- DATABASE_URL
- EXTERNAL_SYNC_TOKEN
- CORS_ORIGINS
- EXTERNAL_SYNC_MIN_INTERVAL_SECONDS

## Validação local antes do deploy

1. Frontend
   - npm run lint
   - npm test -- --watchAll=false
   - npm run build
2. Backend
   - python -m pip_audit -r backend/requirements.txt
   - DATABASE_URL=sqlite:///./backend.db python -c "from backend.main import app; print(app.title)"

## Checklist de segurança

- .env.example sem segredos reais
- Sem logs de credenciais (DATABASE_URL, tokens)
- Endpoint de sync protegido por token interno
- Rate-limit ativo para sync externo
- CORS definido explicitamente por domínio

## Deploy

1. Publicar build da aplicação
2. Aplicar variáveis de ambiente no provedor
3. Subir instância com health check
4. Validar endpoint crítico: /api/overview

## Pós-deploy

- Verificar logs de erro e latência dos endpoints
- Validar sincronização externa manualmente (ambiente controlado)
- Registrar versão e hash de commit implantado