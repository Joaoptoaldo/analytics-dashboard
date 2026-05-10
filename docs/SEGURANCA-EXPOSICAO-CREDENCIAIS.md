# 🔒 SEGURANÇA: Exposição de Credenciais - Histórico de Ações

**Data de Remedição:** 10 de maio de 2026  
**Status:** ⚠️ PARCIALMENTE RESOLVIDO - Histórico ainda contém credenciais

## Resumo do Incidente

O arquivo `.env.production` foi commitado no repositório Git **COM credenciais reais de banco de dados (Neon PostgreSQL)** nos seguintes commits:

| Commit | Hash | Issue |
|--------|------|-------|
| `feat(backend): integrar PostgreSQL com pool e SSL/TLS` | `cb90efd` | ✅ **CREDENCIAIS EXPOSTAS** |
| `organiza a estrutura do projeto...` | `40e30ba` | ⚠️ Placeholders (risco menor) |
| `prepara para o deploy` | `fa15438` | ⚠️ Placeholders (risco menor) |

### Credencial Exposta (Commit cb90efd)
```
postgresql://neondb_owner:npg_kVbLoqca31Kv@ep-mute-sound-acp86gdj-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

---

## ✅ Ações Já Realizadas

### 1. **Arquivo Removido do Rastreamento** (Commit `1882ba8`)
```bash
git rm --cached .env.production
```
- ✅ `.env.production` parou de ser rastreado
- ✅ Commit `1882ba8` documenta a remoção

### 2. **.gitignore Já Configurado Corretamente**
Arquivo `.env.production` já estava no `.gitignore` desde antes:
```
.env
.env.local
.env.*.local
env.production
.env.production  ← Está aqui
.env.production.local
```

### 3. **Template Seguro Criado**
- `.env.production.example` atualizado com valores placeholder
- Todos os valores reais substituídos por template genérico
- Incluído aviso de segurança

---

## ⚠️ O QUE AINDA PRECISA SER FEITO (URGENTE)

### 1. **ROTACIONAR CREDENCIAL NEON IMEDIATAMENTE**
As credenciais abaixo estão EXPOSTAS no histórico Git público:

```
Usuário: neondb_owner
Chave/Token: npg_kVbLoqca31Kv
Host: ep-mute-sound-acp86gdj-pooler.sa-east-1.aws.neon.tech
Banco: neondb
```

**ações obrigatórias:**
1. Acesse [console.neon.tech](https://console.neon.tech)
2. Vá para **Project Settings → Roles**
3. Delete ou resete a senha do role `neondb_owner`
4. Crie um novo role/senha
5. Atualize DATABASE_URL em:
   - Fly.io Secrets
   - Variáveis de ambiente do sistema de deploy
   - `.env.production` (LOCAL APENAS, nunca commitar)

### 2. **REMOVER DO HISTÓRICO GIT (Requer Force Push)**

Infelizmente, `git filter-branch` não conseguiu remover do histórico em Windows. As opções são:

**Opção A: Forçar Limpeza com BFG Repo-Cleaner** (Recomendado)
```bash
# Instalar: https://rtyley.github.io/bfg-repo-cleaner/
bfg --delete-files .env.production
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --mirror --force
```

**Opção B: Reescrever com git-filter-repo** (Se disponível)
```bash
git filter-repo --invert-paths --path .env.production
```

**Opção C: Suportar Histórico com Force Push** (Menos seguro)
- Todos os devs fazem `git pull --rebase`
- Um admin faz `git push --force-with-lease` com commits limpos

### 3. **Notificar Plataformas de Deploy**

Se o repositório é público (GitHub, GitLab):
- O histórico é PÚBLICO
- Qualquer pessoa pode clonar e ver as credenciais
- ⚠️ **Considere comprometido**

Requisitos:
- [ ] Rotate Neon credentials
- [ ] Audit AWS/Neon access logs para atividade suspeita
- [ ] Se repo público, notifique administradores de segurança
- [ ] Considere arquivo .git-crypt ou sealed-secrets

---

## 📋 Checklist de Prevenção Futura

- [ ] **Never commit `.env.production`**: Já adicionado ao `.gitignore`
- [ ] **Use `.env.production.example`**: Como template para documentação
- [ ] **Secret Management Sistema**:
  - [ ] Fly.io Secrets para produção
  - [ ] Vercel/Render Environment Variables
  - [ ] CI/CD secrets (GitHub Actions, GitLab CI, etc.)
- [ ] **Pre-commit Hook**: Adicionar validação
  ```bash
  # .git/hooks/pre-commit
  grep -r "npg_" . --exclude-dir=.git && echo "ERROR: Neon token found" && exit 1
  ```
- [ ] **Audit Regularmente**: `git log -p -- .env*` periodicamente
- [ ] **Documentação**: Manter [`docs/security.md`](docs/) atualizado

---

## 🔗 Referências

- [Neon Security Best Practices](https://neon.tech/docs/security)
- [Git: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [git-filter-repo Documentation](https://github.com/newren/git-filter-repo)

---

## ℹ️ Histórico de Correções

| Data | Ação | Status |
|------|------|--------|
| 2026-05-10 | Detectado `.env.production` com credenciais reais | ✅ Concluído |
| 2026-05-10 | Removido do rastreamento Git (commit `1882ba8`) | ✅ Concluído |
| 2026-05-10 | Atualizado `.env.production.example` com template seguro | ✅ Concluído |
| 2026-05-10 | Criado este documento de mitigação | ✅ Concluído |
| PENDENTE | Rotacionar credenciais Neon | ⏳ URGENTE |
| PENDENTE | Remover do histórico com BFG/filter-repo | ⏳ Depois de rotacionar |
| PENDENTE | Force push se repositório público | ⏳ Coordenar com time |

---

**Responsável:** Sistema de auditoria de segurança  
**Contato:** Revisar antes de fazer force push
