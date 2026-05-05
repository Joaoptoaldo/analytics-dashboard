# Auditoria Analítica Rigorosa do Dashboard

## Resumo Executivo

Status geral após validação cruzada: **confiável com ressalvas corrigidas**.

O dashboard foi validado em três camadas:
- UI renderizada e capturada no navegador.
- Endpoints JSON armazenados em `audit_evidence/`.
- SQL direto comparado contra API e UI.

Resultado atual:
- KPIs: `53` pedidos, `US$ 117.970,71` de receita, `26` clientes, conversão `22,64%`.
- Série temporal: soma da API e do SQL idênticas.
- Distribuição por categoria: contagem total `53`, proporções coerentes.
- Top products: ordenação decrescente confirmada.

## Evidências Coletadas

Arquivos gerados:
- `audit_evidence/overview.json`
- `audit_evidence/sales_monthly.json`
- `audit_evidence/sales_trend_30d.json`
- `audit_evidence/distribution_category.json`
- `audit_evidence/top_products.json`
- `audit_evidence/ticket_average.json`
- `audit_evidence/sql_overview.json`

Capturas visuais atuais do dashboard mostram:
- Receita Total: `$117.970,71`
- Total Pedidos: `53`
- Clientes: `26`
- Conversão: `22.64%`
- Tabela de Pedidos: `53 resultados`
- Série Temporal: `Vendas Temporais - série mensal`
- Distribuição por Categoria: labels percentuais com uma casa decimal após correção

## Validação Cruzada

### 1) KPIs principais

Comparação SQL ↔ API ↔ UI:

| Métrica | SQL | API | UI | Status |
|---|---:|---:|---:|---|
| Total pedidos | 53 | 53 | 53 | OK |
| Receita total | 117970.71 | 117970.71 | 117970.71 | OK |
| Total clientes | 26 | 26 | 26 | OK |
| Conversão | 22.64% | 22.64% | 22.64% | OK |

### 2) Série temporal

SQL direto:
- 2024-05: `1` pedido, `4536.56`
- 2024-06: `10` pedidos, `16194.84`
- 2024-07: `10` pedidos, `17414.40`
- 2024-08: `11` pedidos, `27653.96`
- 2024-09: `10` pedidos, `22135.80`
- 2024-10: `8` pedidos, `30035.15`
- 2026-01: `2` pedidos, `0.00`
- 2026-02: `1` pedido, `0.00`

Validação:
- Soma da série mensal da API = `53` pedidos e `117970.71` de receita.
- Soma do SQL = `53` pedidos e `117970.71` de receita.
- Divergência = `0`.

Observação:
- Existem meses com `revenue = 0` e `orders > 0` por causa dos registros de mercado com preço zero. Isso é dado real do dataset atual, mas merece monitoramento como outlier operacional.

### 3) Distribuição por categoria

Contagem API/SQL:
- groceries: `12`
- beauty: `11`
- mens-watches: `10`
- home-decoration: `10`
- kitchen-accessories: `7`
- Market: `3`

Soma total:
- `53`

Percentuais da UI após correção:
- `22.6%`, `20.8%`, `18.9%`, `18.9%`, `13.2%`, `5.7%`

A soma exibida dos rótulos fica próxima de `100%` e já não sofre o arredondamento inteiro que gerava distorção visual anterior.

### 4) Top products

SQL direto e API estão alinhados na mesma ordem decrescente por receita:
1. Eclipse Systems - `4883.41`
2. Bright Future - `4713.82`
3. Infinity Group - `4700.76`
4. UrbanStyle - `4652.19`
5. Synergy Partners - `4636.24`
6. CloudOps - `4536.56`
7. Radiant Ventures - `4504.73`
8. SmartLabs - `4459.59`
9. Visionary Labs - `4432.26`
10. VidaCare - `4416.23`

Status: ordenação correta, sem inversão de ranking.

## Inconsistências Encontradas e Corrigidas

### 1) Tabela de pedidos misturando universo sintético com universo real
- Sintoma: a tabela mostrava `103 resultados` enquanto os KPIs exibiam `53`.
- Causa raiz: `backend/services/products.py` não filtrava `is_synthetic == False`.
- Correção mínima: adicionado filtro no query base do serviço de produtos.
- Resultado pós-correção: tabela passou a mostrar `53 resultados`, alinhada aos KPIs.
- Impacto: alto, porque misturava universos diferentes na mesma tela.

### 2) Labels da pizza chart arredondadas para inteiro
- Sintoma: fatias exibidas como `23%`, `21%`, `19%`, `19%`, `13%`, `6%` somavam `101%` visualmente.
- Causa raiz: `toFixed(0)` no rótulo da pizza.
- Correção mínima: trocado para `toFixed(1)`.
- Resultado pós-correção: labels agora aparecem como `22.6%`, `20.8%`, `18.9%`, `18.9%`, `13.2%`, `5.7%`.
- Impacto: médio, por distorção visual da leitura de proporção.

### 3) Conexão do frontend com a API no ambiente de auditoria
- Sintoma: UI presa em `Carregando...` e requisições a `localhost:8000` falhando.
- Causa raiz: o Vite não proxyava `/api` e `VITE_API_BASE_URL` apontava para origem direta do backend.
- Correção mínima:
  - `vite.config.ts` com proxy para `/api` e `/internal`.
  - `.env.local` com `VITE_API_BASE_URL=/api`.
- Resultado: a UI passou a carregar corretamente e refletir os dados reais.
- Impacto: alto, pois impedia a auditoria visual.

## Testes Controlados

Cenários executados em SQLite temporário:
- `small_2_rows`
- `same_day_concentrated`
- `gaps_series`
- `multi_category`

Resultados observados:
- `sales_monthly`: sempre `valid` quando havia registros com data.
- `sales_trend`: série contínua gerada com janela de `30` pontos.
- `distribution/category`: percentuais sempre coerentes com a contagem.
- `top/products`: sempre ordenado descendentemente por receita.
- `products` paginado: totais iguais ao número de registros inseridos.

Observação do teste `multi_category`:
- Percentuais arredondados podem somar `99.99%` por efeito de ponto flutuante, o que é aceitável para exibição, mas deve ser considerado ao interpretar labels.

## Veredito Final

### Dados confiáveis?
**Sim**, após correções locais aplicadas e revalidação numérica.

### Visualizações confiáveis?
**Sim**, com duas correções importantes já aplicadas:
- tabela de pedidos alinhada ao mesmo universo dos KPIs;
- labels do gráfico de pizza com precisão adequada.

### Risco residual
- Há meses com receita zero e pedidos não-zero em dados de mercado; isso é dado real do dataset atual, mas deve ser monitorado como possível outlier de negócio.

## Arquivos tocados nesta auditoria
- `backend/services/products.py`
- `src/Dashboard.tsx`
- `vite.config.ts`
- `.env.local`
- `controlled_dataset_audit.py`
- `audit_evidence/*`

## Conclusão
A auditoria encontrou e corrigiu divergências reais de visualização e de recorte de dados. Depois das correções, os três níveis ficaram consistentes: **SQL = API = UI** para os KPIs e os gráficos principais.
