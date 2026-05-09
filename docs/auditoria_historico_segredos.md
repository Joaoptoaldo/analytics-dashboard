# Auditoria de Histórico de Segredos

## Data

- 2026-05-01

## Método aplicado

- Varredura em todo o histórico Git com git log -G usando padrões de alta confiança:
  - AWS Access Key ID (AKIA...)
  - GitHub PAT (ghp_...)
  - Google API Key (AIza...)
  - Blocos de chave privada (BEGIN ... PRIVATE KEY)
  - URLs com credenciais embutidas (postgres://user:pass@..., mongodb://user:pass@...)

## Resultado

- 0 commits com match para os padrões analisados
- Sem evidência de segredo histórico com os padrões de alta confiança

## Limitação

- Scanner dedicado (Gitleaks) não disponível no ambiente durante a execução
- Recomendação: executar Gitleaks no pipeline ou em estação com ferramenta instalada para cobertura adicional