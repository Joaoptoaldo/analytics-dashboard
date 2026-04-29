# Contexto do Projeto

Você está me ajudando a construir o **Dashboard de Análise**, um sistema full stack com foco em visualização de dados, KPIs, filtros, tabelas e gráficos com aparência de produto SaaS.

O projeto já possui um **MVP funcional** e o objetivo agora é evoluir a base atual com mais consistência arquitetural, melhor documentação, backend mais robusto e experiência mais próxima de produção.

---

# Estado Real do Repositório

## Frontend atual

Stack em uso hoje:

* React 19
* Vite
* TypeScript
* Tailwind CSS v4
* shadcn/ui + Radix UI
* Recharts
* SWR
* Lucide React

Arquivos principais atuais:

* `src/main.tsx`
* `src/App.tsx`
* `src/Dashboard.tsx`
* `hooks/use-dashboard.ts`
* `components/ui/*`
* `app/globals.css`

Observações importantes:

* O projeto **não está em JavaScript puro**; a base atual usa TypeScript.
* Há arquivos residuais em `app/` que vieram de uma estrutura inspirada em Next.js, mas o entrypoint real hoje é o Vite em `src/main.tsx`.
* A UI principal atual está concentrada em `src/App.tsx` e `src/Dashboard.tsx`.
* O CSS global ativo está sendo importado de `app/globals.css` em `src/main.tsx`.
* Ainda existem duplicações utilitárias e arquivos legados que devem ser tratados com cuidado antes de qualquer limpeza estrutural.

## Backend atual

Stack em uso hoje:

* Python
* FastAPI
* Uvicorn
* CORS configurado

Arquivos principais atuais:

* `backend/main.py`
* `backend/pyproject.toml`

Observações importantes:

* O backend estava originalmente concentrado em um único arquivo, mas foi evoluindo: hoje já existe integração com `models/`, `services/` e `routers/` e uso de SQLAlchemy para persistência.
* Produtos externos podem ser sincronizados e persistidos em SQLite através do endpoint `POST /api/external-products/sync`.
* A base foi atualizada para que dados apresentados no dashboard venham do banco, não mais de um dataset em memória. Ao trabalhar com o backend, preserve compatibilidade com os endpoints existentes.

---

# Direção Técnica do Projeto

## O que já existe

Hoje o projeto já entrega:

* sidebar responsiva
* dashboard com KPIs
* gráfico de linha
* gráfico de pizza
* tabela com paginação
* filtros funcionais conectados ao backend
* ordenação na tabela
* consumo de API com SWR
* seed mock consistente para demonstração
* contrato frontend/backend funcional via endpoints FastAPI

## O que ainda é objetivo de evolução

Evoluções planejadas (prioritárias):

* consolidar a modularização do backend (rotas, services, modelos separados)
* preparar migração para PostgreSQL a partir de uma camada de acesso bem definida
* separar melhor os componentes de dashboard e reduzir duplicações
* adicionar autenticação e autorização
* melhorar performance do bundle frontend
* fortalecer documentação e testes automatizados

---

# Estrutura Atual do Projeto

```txt
dashboard-de-analise/
├── .github/
│   └── IA-instruções.md
├── app/
│   ├── globals.css
│   └── page.tsx
├── backend/
│   ├── main.py
│   ├── pyproject.toml
│   └── uv.lock
├── components/
│   ├── theme-provider.tsx
│   └── ui/
├── hooks/
│   ├── use-dashboard.ts
│   ├── use-mobile.ts
│   └── use-toast.ts
├── lib/
│   ├── utils.js
│   └── utils.ts
├── public/
│   └── icon.svg
├── src/
│   ├── App.tsx
│   ├── Dashboard.tsx
│   └── main.tsx
├── styles/
│   └── globals.css
├── index.html
├── jsconfig.json
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

---

# Regras de Colaboração

## Regra principal

Antes de alterar código, instalar dependências, refatorar estrutura ou tomar decisão com impacto arquitetural:

1. explique o que pretende fazer
2. diga por que isso faz sentido no contexto atual do projeto
3. destaque impactos, tradeoffs e arquivos afetados
4. aguarde minha autorização explícita

Autorizações válidas:

* `pode fazer`
* `vai`
* `sim`
* `segue`
* ou equivalente

## Quando eu pedir ajuda

* explique a lógica antes do código
* conecte a solução à arquitetura atual do projeto
* diferencie claramente:
  * estado atual
  * dívida técnica
  * direção futura
* aponte riscos técnicos e consequências
* priorize soluções limpas e sustentáveis
* evite gambiarra

## Quando sugerir código

* informe quais arquivos serão alterados
* diga se a mudança é local ou se impacta outras partes
* avise quando houver débito técnico sendo criado
* se houver mais de um caminho razoável, apresente as opções antes de implementar

## Se eu errar algo

* corrija de forma didática
* explique a causa raiz
* me ajude a evitar repetir o erro
* mostre como a correção se encaixa na arquitetura geral

---

# Regras Técnicas

## Sobre a stack

* considere **TypeScript** como padrão atual do frontend
* não proponha voltar para JavaScript sem alinhamento explícito
* preserve Vite como bundler atual
* use a arquitetura existente como ponto de partida, não como se já fosse a arquitetura final

## Sobre frontend

* preservar o design system baseado em shadcn/ui e Radix
* evitar duplicação de hooks, utils e estilos
* preferir componentização clara quando isso realmente melhorar manutenção
* não criar páginas falsas só para parecer completo
* filtros devem continuar sendo reais, não decorativos
* tratar `app/` como resíduo de transição até que haja decisão explícita de remover ou reaproveitar essa estrutura

## Sobre backend

* manter compatibilidade com o contrato atual consumido pelo frontend
* evitar quebrar endpoints existentes sem avisar antes
* o seed mock foi substituído progressivamente por persistência (SQLite + SQLAlchemy). Ao propor mudanças, documente o impacto e migrações necessárias
* quando propor persistência adicional, priorizar soluções que facilitem migração para bancos gerenciados

## Sobre documentação

* sempre atualizar docs quando a implementação mudar de direção
* nunca descrever como “pronto” algo que ainda é apenas objetivo futuro
* diferenciar claramente visão do produto versus código já implementado
* não citar arquivos, módulos ou fluxos que não existam mais no repositório atual

---

# O que Evitar

* assumir que a arquitetura alvo já está pronta
* misturar documentação aspiracional com documentação operacional
* criar estruturas grandes sem necessidade imediata
* instalar pacotes sem explicar a justificativa
* refatorar por estética sem ganho claro
* manter arquivos duplicados por muito tempo
* esconder riscos de manutenção

---

# Commits

Quando sugerir commits, usar Conventional Commits.

Exemplos:

* `feat:`
* `fix:`
* `chore:`
* `refactor:`
* `docs:`
* `test:`

Nunca sugerir commits genéricos.

---

# Orientação de Evolução

Prioridades gerais do projeto:

1. alinhar documentação com o código real
2. reduzir inconsistências e duplicações
3. modularizar frontend e backend sem refatoração destrutiva
4. introduzir persistência real
5. preparar autenticação e expansão funcional
6. melhorar qualidade de build, performance e deploy

Ao sugerir próximos passos, priorize:

* coerência arquitetural
* manutenção futura
* clareza para portfólio profissional
* progressão incremental sem quebrar o MVP atual
* comunicação clara sobre o que é código real versus objetivo futuro
* sempre destacar o impacto e tradeoffs de cada mudança proposta
