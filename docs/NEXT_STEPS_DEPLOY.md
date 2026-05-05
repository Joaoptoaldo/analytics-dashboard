# Proximos passos de deploy

Seu sistema esta aprovado para producao. O passo seguinte e escolher um dos caminhos de deploy abaixo e aplicar as validacoes finais.

## Opcao 1: Render.com

Use o arquivo `render.yaml` como base do servico e configure as variaveis de ambiente no painel da plataforma.

Variaveis obrigatorias:
- `DATABASE_URL`
- `CORS_ORIGINS`
- `EXTERNAL_SYNC_TOKEN`
- `ALLOW_SEED=false`

Validacoes apos o deploy:
- `GET /health`
- `GET /readiness`
- `GET /api/overview`
- `GET /api/sales`

## Opcao 2: Fly.io

Use os arquivos `fly.toml` e `fly.toml.prod` como referencia para a publicacao.

Antes de publicar:
- Defina secrets reais, sem placeholders.
- Garanta que o banco seja PostgreSQL.
- Mantenha `CORS_ORIGINS` restrito aos dominios permitidos.
- Use um `EXTERNAL_SYNC_TOKEN` forte, com no minimo 32 caracteres.
- Mantenha `ALLOW_SEED=false` em producao.

## Checklist final

- O container sobe sem erros.
- O backend responde em `/health` e `/readiness`.
- As rotas principais da API retornam dados reais.
- Nenhuma configuracao de desenvolvimento ficou exposta em producao.
