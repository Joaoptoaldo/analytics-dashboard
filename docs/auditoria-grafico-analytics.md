# Auditoria Técnica do Gráfico de Analytics

Data da auditoria: 2026-05-01

Escopo auditado:
- Gráfico Vendas Mensais em [src/pages/Analytics.tsx](src/pages/Analytics.tsx#L105)
- Gráfico Receita Média em [src/pages/Analytics.tsx](src/pages/Analytics.tsx#L137)
- Fonte de dados em [hooks/use-dashboard.ts](hooks/use-dashboard.ts#L193)
- Cálculo backend em [backend/services/analytics.py](backend/services/analytics.py#L351)

Dados reais utilizados na validação:
- sales/monthly: month 2025-04, revenue 64667.90, orders 100
- metrics/ticket-average: month 2025-04, avg_ticket 646.68, orders 100

## 1) Integridade Visual

Resultado:
- Para o dataset atual, não há distorção do desenho em relação aos dados, pois existe apenas 1 ponto em cada série.

Riscos de distorção identificados no componente:
- A linha usa interpolação monotone em [src/pages/Analytics.tsx](src/pages/Analytics.tsx#L110) e [src/pages/Analytics.tsx](src/pages/Analytics.tsx#L142). Em séries com poucos pontos ou alta volatilidade, essa suavização pode sugerir curvaturas intermediárias que não existem nos valores brutos.
- O eixo Y está em auto-scale em [src/pages/Analytics.tsx](src/pages/Analytics.tsx#L108) e [src/pages/Analytics.tsx](src/pages/Analytics.tsx#L140), sem domínio fixo iniciando em zero. Em cenários futuros, isso pode aumentar visualmente pequenas variações.

## 2) Validação de Métricas

Conferência ponto a ponto endpoint versus SQL bruto:
- Mismatches em Vendas Mensais: 0
- Mismatches em Receita Média: 0

Métricas calculadas na auditoria com base na série de receita mensal:
- Média: 64667.90
- Desvio padrão populacional: 0.00
- CAGR: não aplicável com 1 ponto temporal

Observação crítica de semântica:
- O endpoint de ticket médio calcula AVG(revenue) por mês, conforme implementação em [backend/services/analytics.py](backend/services/analytics.py#L351).
- Isso é média de receita por registro, não ticket médio real por cliente único.

## 3) Consistência Lógica

Adequação do tipo de gráfico:
- Linha temporal é adequada para séries mensais quando há histórico suficiente.
- Com apenas 1 mês, o gráfico de linha perde significado analítico e funciona apenas como exibição de ponto único.

Discrepâncias entre narrativa visual e realidade estatística:
- Inconsistência de nomenclatura: Receita Média no frontend pode ser interpretada como ticket médio de negócio, mas tecnicamente o cálculo atual é média simples de revenue por registro.

## Conclusão

Inconsistências encontradas:
1. Semântica da métrica ticket médio é potencialmente enganosa para leitura de negócio.
2. Risco de indução visual em cenários futuros por linha suavizada e eixo Y sem baseline explícito.

Precisão numérica atual:
- Os pontos plotados e eixos conferem com os valores brutos disponíveis no momento da auditoria.