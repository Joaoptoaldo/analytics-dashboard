# Runbook de Rotação de Credenciais

## Quando rotacionar

- Suspeita de vazamento
- Mudança de equipe com acesso privilegiado
- Janela periódica (recomendado: mensal para tokens críticos)

## Escopo mínimo

- EXTERNAL_SYNC_TOKEN
- Credenciais do banco (DATABASE_URL)
- Qualquer chave de API de integração externa

## Procedimento

1. Gerar novo segredo em cofre seguro
2. Atualizar segredo no ambiente de staging
3. Validar aplicação em staging
4. Aplicar segredo em produção
5. Reiniciar serviço para recarregar env
6. Revogar segredo antigo

## Validação após rotação

- /api/overview responde 200
- /api/external-products/sync exige token válido
- Logs sem erros de autenticação inesperados

## Resposta a incidente

1. Isolar credencial comprometida
2. Rotacionar imediatamente no provedor
3. Revisar histórico Git e logs de build/deploy
4. Auditar acessos nos últimos 7 dias
5. Documentar causa raiz e ações corretivas

## Evidências a registrar

- Data/hora da rotação
- Responsável
- Ambientes afetados
- Serviços validados
- Número do incidente/ticket