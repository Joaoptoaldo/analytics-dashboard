# TODO: Roadmap do Dashboard de Analise

Status: em evolucao

## 1. Alinhamento de base

- [x] Ajustar o projeto para Vite puro
- [x] Consolidar o frontend principal em `src/`
- [x] Atualizar a documentacao para refletir o estado real do repositorio
- [ ] Remover residuos de abordagem hibrida entre `app/` e `src/`

## 2. Organizacao do frontend

- [ ] Quebrar `src/Dashboard.tsx` em componentes menores
- [ ] Consolidar hooks e utils duplicados
- [ ] Revisar estados de loading, erro e empty state
- [ ] Melhorar formatacao de moeda, datas e labels

## 3. Dados e integracao

- [x] Conectar frontend ao backend com SWR
- [x] Implementar filtros reais no consumo da API
- [x] Implementar paginacao e ordenacao na tabela
- [ ] Centralizar contratos e tipos da API

## 4. Backend

- [x] Disponibilizar API FastAPI com seed mock
- [ ] Separar rotas, regras de negocio e camada de dados
- [ ] Introduzir persistencia com SQLite
- [ ] Preparar migracao futura para PostgreSQL
- [ ] Padronizar schemas de resposta e erros

## 5. Produto

- [ ] Adicionar autenticacao inicial
- [ ] Criar navegacao real para modulos da sidebar
- [ ] Implementar exportacao CSV
- [ ] Definir estrutura inicial para exportacao PDF

## 6. Qualidade

- [ ] Adicionar testes principais do frontend
- [ ] Adicionar testes basicos do backend
- [ ] Revisar performance do bundle
- [ ] Documentar setup, arquitetura e deploy

## 7. Deploy

- [ ] Definir variaveis de ambiente do frontend
- [ ] Definir variaveis de ambiente do backend
- [ ] Preparar frontend para deploy em Vercel
- [ ] Preparar backend para deploy em Render, Railway ou VPS
