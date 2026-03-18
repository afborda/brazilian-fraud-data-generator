# Gap Analysis — Brazilian Fraud Data Generator v4.8

> **Data da análise**: 2026-03-17
> **Branch analisada**: `v4-beta` (v4.8.0, 6 commits à frente de main)
> **Metodologia**: leitura do código-fonte + cruzamento com TURNOS_IMPLEMENTACAO.md, RESUMO_EXECUTIVO.md e ROTEIRO_PRODUCAO.md

---

## TL;DR

O projeto está **sólido tecnicamente**. O core gerador, o pipeline de enriquecimento e os padrões de fraude foram todos implementados. Os gaps remanescentes se concentram em **3 áreas**:

1. **Pequenos itens de qualidade de dados** — 4 sub-tarefas abertas dentro de turnos marcados como concluídos
2. **Ferramentas de validação** — 2 scripts de validação que nunca foram criados
3. **Produção / Infra** — nenhuma das 8 fases do ROTEIRO_PRODUCAO foi executada

---

## 1. Status Geral dos Turnos de Implementação

| Turno | Tema | Status declarado | Status real |
|-------|------|:---:|:---:|
| T0 | Baseline & métricas | ✅ | ✅ |
| T1 | Realismo temporal | ✅ | ✅ (latência de fraude aberta, ver T1.1) |
| T2 | Realismo geográfico | ✅ | ✅ (validações nunca rodadas, ver T2.1) |
| T3 | Card Testing + Velocity | ✅ | ✅ |
| T4 | Consistência comportamental | ✅ | ⚠️ (account ramp-up faltando, ver T4.1) |
| T5 | Ride-Share novos fraudes | ✅ | ✅ (validações nunca rodadas) |
| T6 | Fraud Rings | ✅ | ✅ |
| T7 | Ajustes finos | ✅ | ⚠️ (AUTOFRAUDE e check_schema.py, ver T7.1) |
| TSN | Pipeline de Risco | ✅ | ✅ |
| TPRD1 | Campos de contexto faltantes | ✅ | ⚠️ (num_failed_auth_attempts faltando) |
| TPRD2 | Biometria (tier pago) | ✅ | ✅ |
| TPRD3 | PIX Fase 2 | ✅ | ✅ |
| TPRD4 | Enricher pipeline | ✅ | ✅ |
| TPRD5 | CI/CD + brazildata-infra | ✅ | ⚠️ (workflows criados, produção não executada) |

---

## 2. Gaps de Código — Detalhamento

### 2.1 T1 — Latência de Fraude (não implementado)

**O que está faltando:**
`ENGENHARIA_SOCIAL` e `PHISHING` deveriam ter um gap temporal entre "data de comprometimento" e "primeiro uso", mas hoje a fraude começa imediatamente.

**Campos previstos no schema:**
- `compromise_date: datetime` — data em que o dado foi comprometido
- `first_fraud_date: datetime` — data do primeiro uso fraudulento (2–7 dias depois)

**Impacto**: modelos de sequência (LSTM/RNN) não conseguem aprender esse padrão; o gap temporal é um feature muito relevante para ENGENHARIA_SOCIAL real.

**Arquivo alvo**: `src/fraud_generator/config/fraud_patterns.py` + `src/fraud_generator/generators/transaction.py`

---

### 2.2 T2 — Validações geográficas nunca rodadas

Os campos `is_impossible_travel` e `location_cluster` estão implementados no código (`cli/workers/tx_worker.py:123`), mas as validações do turno nunca foram executadas:

- [ ] Confirmar que >90% das transações legítimas estão dentro do cluster geográfico do cliente
- [ ] Confirmar que `is_impossible_travel=True` aparece em ~2% das fraudes de CONTA_TOMADA

**Ação**: rodar `validate_realism.py` com foco em geo-distribution e verificar os números.

---

### 2.3 T4 — Account Ramp-Up (não implementado)

**O que está faltando:**
Clientes novos (dias 1–30) deveriam ter valores de transação progressivamente maiores:

```
Dias  1–7  → máx R$ 200
Dias  8–30 → máx R$ 1.000
Dias 31+   → padrão normal do perfil
```

**Por que importa**: dados sem ramp-up fazem novos clientes parecerem idênticos a clientes antigos — um dos features mais importantes em sistemas de fraude reais.

**Arquivo alvo**: `src/fraud_generator/generators/customer.py` (campo `account_age_days`) + `src/fraud_generator/generators/transaction.py` (gate de valor por `account_age_days`).

---

### 2.4 T7 — AUTOFRAUDE não foi reclassificado

**Situação atual** (`src/fraud_generator/config/transactions.py:41`):
```python
'AUTOFRAUDE': 8,        # First-party fraud
'FRAUDE_AMIGAVEL': 5,   # Friendly fraud
```

**O que foi planejado**: remover `AUTOFRAUDE` como tipo isolado (prevalência real ~0%) ou fundir com `FRAUDE_AMIGAVEL`. Com os dois tipos coexistindo e somando 13% do peso, a distribuição distorce modelos de ML que aprendem que 8% dos casos são first-party fraud puro — algo raro na prática brasileira.

**Ação recomendada**: mesclar `AUTOFRAUDE` em `FRAUDE_AMIGAVEL` (único tipo com 10–12%) e ajustar o peso total para manter a fraud rate global no target.

---

### 2.5 TPRD1 — `num_failed_auth_attempts` faltando

Este campo foi especificado no TPRD1 mas **não foi implementado** em nenhum arquivo do `src/`:

```
num_failed_auth_attempts: int  # tentativas de auth falhadas na sessão
```

É um campo de signal médio-alto: ATO real frequentemente vem precedido de múltiplas tentativas de login falhadas. Ausência no output significa que modelos não conseguem treinar nesse pattern.

**Arquivo alvo**: `src/fraud_generator/generators/session_context.py` + serializado em `transaction.py`.

---

### 2.6 `validate_correlations.py` — nunca foi criado

O script de validação das 15 regras de correlação comportamental foi mencionado em TSN como "what NOT done" e nunca implementado. Sem ele, não há como verificar automaticamente que:

- `MALWARE_ATS` ativa quando emulator + rooted + zero typing + zero accel
- `ATO` ativa quando new_device + IP_mismatch + session < 60s + inactivity > 168h
- `FALSA_CENTRAL` ativa quando active_call + dest_account_age < 7 dias
- `CONTA_LARANJA` ativa quando multiple_accounts + new_dest_account

**Onde criar**: `scripts/validate_correlations.py` ou `tests/unit/test_correlation_rules.py`

---

### 2.7 `check_schema.py` desatualizado

O T7 planejou atualizar `check_schema.py` para validar todos os campos novos (T3, T4, T5, T6, TPRD1–3), mas esse update nunca aconteceu. O script valida o schema da época v3.x e vai deixar passar ou rejeitar campos incorretamente.

**Campos sem cobertura no check_schema atual:**
- `card_test_phase`, `velocity_burst_id`, `distributed_attack_group` (T3)
- `customer_velocity_z_score`, `new_merchant`, `new_beneficiary` (T4)
- `route_deviation_km`, `refund_count_30d`, `payment_dispute_flag` (T5)
- `fraud_ring_id`, `ring_role`, `recipient_is_mule` (T6)
- `fraud_signals`, `ip_location_matches_account`, `classe_social`, `cliente_perfil` (TPRD1)
- `cpf_hash_pagador`, `cpf_hash_recebedor`, `pacs_status`, `motivo_devolucao_med`, `is_devolucao` (TPRD3)

---

## 3. Gaps de Ferramentas de Validação

### 3.1 Nenhuma validação de pós-turno foi executada

O `TURNOS_IMPLEMENTACAO.md` lista checklists de validação em cada turno (rodar dataset, verificar distribuições, checar correlações). Com exceção do T0 (baseline) e T1 (medições de pico temporal), **nenhuma validação dos turnos T2–T7 e TPRD1–5 foi executada**.

Isso significa que o código foi implementado mas não sabemos se os invariantes estão sendo mantidos:

| Check | Arquivo de validação | Status |
|-------|---------------------|:---:|
| >90% txns legítimas no cluster geo | `validate_realism.py` (geo section) | ❌ não rodado |
| `is_impossible_travel=True` em ~2% ATO | manual ou script | ❌ não rodado |
| `customer_velocity_z_score > 5` em >80% ATO | manual ou script | ❌ não rodado |
| Novos merchants em >90% fraudes cartão | manual ou script | ❌ não rodado |
| Black Friday gera spike visível | manual ou script | ❌ não rodado |
| Fraud rings formam clusters no grafo | `scripts/validate_correlations.py` | ❌ script não existe |
| `check_schema.py` passa zero erros | `check_schema.py` | ❌ script desatualizado |

**Ação recomendada**: criar uma suite de smoke-tests de qualidade de dados — `tests/quality/test_data_invariants.py` — que gere 10k registros com seed fixo e verifique as proporções esperadas.

---

### 3.2 TSTR benchmark desatualizado

O `synthfin_tstr_benchmark.py` foi criado antes dos turnos T2–T7 e validou AUC gap = 0% para o schema v3.x. Com 30+ novos campos e padrões de fraude mais sofisticados, o benchmark não foi re-executado para confirmar que a qualidade ML se manteve.

**Risco**: se algum enricher introduziu correlações espúrias, o AUC gap pode ter aumentado — e não saberíamos.

---

## 4. Gaps de Produto / Arquitetura

### 4.1 `pipeline/` folder não existe

TPRD4 planejou criar:
```
pipeline/
├── context.py           # TransactionContext dataclass intermediário
└── transaction_pipeline.py  # orquestrador
```

O que foi criado (`enrichers/`) resolve o mesmo problema de outra forma — via `pipeline_factory.py`. Porém, o `TransactionContext` dataclass intermediário **não existe**: os enrichers operam diretamente sobre o dicionário de transação (`dict`), o que torna mais difícil verificar tipos em compile time e gera acoplamento implícito via string keys.

**Impacto**: baixo para funcionamento, mas médio para manutenibilidade — adicionar um novo enricher requer conhecer as string keys implícitas.

---

### 4.2 Enricher pipeline não integrado ao `TransactionGenerator` principal

O `generate_with_pipeline()` existe, mas o `TransactionGenerator.generate_transaction()` monolítico continua sendo o caminho principal. Os enrichers ficam como camada opcional, não como substituição.

Isso cria **duplicação de lógica**: campos como `network_type` e `language_locale` são calculados **tanto** em `transaction.py:1116` **quanto** em `enrichers/risk.py:89`. Se um for atualizado, o outro fica dessincronizado.

**Arquivos com duplicação confirmada:**
- `network_type` — `transaction.py:1116-1122` e `enrichers/risk.py:89-92`
- `language_locale` — `transaction.py:1124-1131` e `enrichers/risk.py:94-101`

---

### 4.3 Redis caching opcional mas não documentado no README

O `redis_cache.py` está implementado e a flag `--redis-url` existe na CLI, mas:
- O README não menciona como configurar Redis para persistência de índice
- O `docker-compose.yml` não tem serviço Redis por padrão (só no docker-compose.server.yml)
- Não há teste de integração verificando que o índice sobrevive a reinicializações

---

### 4.4 Schema mode (`SchemaEngine`) sem suporte a ride-share completo

O `SchemaEngine` (`src/fraud_generator/schema/engine.py`) suporta banking e ride, mas:
- `rideshare_full.json` usa apenas campos básicos — os campos novos de T5 (`route_deviation_km`, `refund_count_30d`, etc.) não estão no schema declarativo
- O `banking_full.json` foi atualizado para v2.0/v2.1, mas o schema em `docs/documentodeestudos/brazildata_schema.json` pode estar desatualizado

---

## 5. Gaps de Infraestrutura / Produção

Este é o maior gap não executado. O **ROTEIRO_PRODUCAO.md** lista 8 fases completas e nenhuma foi iniciada.

### 5.1 O que está pronto (artefatos criados)

| Artefato | Localização | Estado |
|----------|-------------|:---:|
| Workflows GitHub Actions (4) | `.github/workflows/` | ✅ criados |
| `brazildata-infra/` (estrutura completa) | repo local | ✅ estrutura pronta |
| `ROTEIRO_PRODUCAO.md` (passo a passo) | `docs/` | ✅ documentado |
| Schema de serviços (Traefik, PostgreSQL, Redis, MinIO) | `brazildata-infra/services/` | ✅ configurado |

### 5.2 O que precisa ser executado

```
FASE 1 — Adicionar workflows nos repos corretos
  [ ] deploy-product.yml → repo synthfin-api (existe no CORE, não no API repo)
  [ ] deploy-site.yml → repo synthfin-web

FASE 2 — Popular synthfin-infra no GitHub
  [ ] sed: synthlab.io → synthfin.com.br
  [ ] sed: brazildata → synthfin
  [ ] git init + remote + push

FASE 3 — Chave SSH CI/CD dedicada
  [ ] ssh-keygen para synthfin-cicd (separada da pessoal)

FASE 4 — Secrets GitHub (3 repos)
  [ ] VPS_HOST, VPS_USER, VPS_SSH_KEY, VPS_SSH_PORT
  [ ] GHCR_TOKEN, DOCKERHUB_USERNAME, DOCKERHUB_TOKEN

FASE 5 — Provisionar VPS OVH
  [ ] Criar .env com senhas fortes
  [ ] Rodar setup.sh (instala Docker, Traefik, serviços, monitoramento, backup)
  [ ] Testar SSH na porta 2222 antes de fechar sessão root

FASE 6 — Configurar DNS synthfin.com.br
  [ ] A records: @, api, dash, minio → IP VPS

FASE 7 — Validar produção
  [ ] https://api.synthfin.com.br/health → 200
  [ ] SSL A+ no SSL Labs
  [ ] audit-security.sh → zero erros

FASE 8 — Stripe webhook
  [ ] Endpoint configurado em api.synthfin.com.br/webhooks/stripe
  [ ] Signing secret no .env
```

### 5.3 Repos — situação real (verificado em 2026-03-17)

O mapa de repos prevê repos separados, mas a estrutura local é diferente:

| Repo | Localização local | Remote GitHub | Estado |
|------|-------------------|:---:|:---:|
| `synthfin-core` (público) | `brazilian-fraud-data-generator/` | ✅ existe | ✅ |
| `synthfin-api` (privado) | `synthfin/api/` (subfolder) | ❌ sem remote | ⚠️ código existe, não subido |
| `synthfin-web` (privado) | `synthfin/web/` (subfolder) | ❌ sem remote | ⚠️ código existe, não subido |
| `synthfin-infra` (privado) | `brazildata-infra/` | ✅ `github.com/afborda/synthfin-infra` | ✅ |
| `synthfin-saas` (privado) | `synthfin-saas/` | ✅ `github.com/afborda/synthfin-saas` | ✅ |

**Situação real**: `synthfin/` é um monorepo local com `api/`, `web/` e `saas/` dentro, mas **sem `git init` nem remote configurado**. O código existe mas nunca foi pushed para o GitHub.

**Decisão pendente**: manter monorepo (`synthfin/` único repo com subpastas) ou separar em repos individuais conforme o ROTEIRO planeja. Os workflows em `.github/workflows/` foram escritos assumindo repos separados.

---

## 6. Gaps de Documentação

### 6.1 INDEX.md desatualizado

O `git status` mostra `M docs/INDEX.md` (modificado mas não commitado). O arquivo está desatualizado em relação ao estado atual do projeto — `ROTEIRO_PRODUCAO.md` foi adicionado mas não está linkado no INDEX.

**Ação**: commitar o INDEX.md com referência ao ROTEIRO_PRODUCAO.md e a este GAP_ANALYSIS.md.

### 6.2 RESUMO_EXECUTIVO.md desatualizado

O `RESUMO_EXECUTIVO.md` em `docs/analysis/` foi escrito em **Janeiro de 2026** e reflete o estado pré-v4.2. Os problemas listados como "críticos" (P1–P6) foram todos resolvidos:

- P1 (fraude simplista) → resolvido em T3–T7
- P2 (random.choices por transação) → resolvido via WeightCache
- P3 (CSV/Parquet OOM) → resolvido via streaming writer
- P4 (sem retry MinIO) → resolvido
- P5 (campos None) → resolvido
- P6 (sem histórico do cliente) → resolvido em T4

O documento está tecnicamente **obsoleto** — pode confundir novos colaboradores que acham que o projeto ainda tem esses problemas críticos.

**Ação**: ou arquivar (`docs/analysis/archive/`) ou atualizar com o estado atual.

### 6.3 ARCHITECTURE.md vs código atual

O `ARCHITECTURE.md` ainda descreve `TransactionGenerator` como o ponto central. Com a adição do enricher pipeline (TPRD4), a arquitetura real tem duas rotas:
1. `TransactionGenerator.generate_transaction()` — path monolítico legado
2. `generate_with_pipeline()` via `enrichers/pipeline_factory.py` — path modular

Isso não está documentado em ARCHITECTURE.md.

---

## 7. O Que Está Bem Implementado (referência)

Para contextualizar os gaps, o que está **sólido e sem gaps**:

| Componente | Evidência de qualidade |
|------------|----------------------|
| CPF geração/validação | `validators/cpf.py` — mod-11 BACEN compliant |
| PIX BACEN fields | 8 campos incluindo `end_to_end_id`, `ispb_*`, `cpf_hash_*`, `pacs_status` |
| Fraud scoring pipeline | `score.py` — 17 sinais ponderados, 0–100, testes unitários |
| Behavioral profiles | 7 transação + 7 ride, cada um com distribuições específicas |
| Fraud ring detection | `_RingRegistry` singleton, `fraud_ring_id`, `ring_role`, `recipient_is_mule` |
| Enricher pipeline | 10 enrichers em `enrichers/`, `pipeline_factory.py` |
| Biometric fields | `biometric.py` — null em OS tier, 10 campos em tier pago |
| Compression | gzip/zstd/snappy, strategy pattern, auto-detect por extensão |
| Paralelismo | ProcessPool (CPU) + ThreadPool (I/O), seed determinístico por worker |
| Formatos de saída | 8 formatos: JSONL, JSON, CSV, TSV, Parquet, Arrow, Database, MinIO |
| Testes | 14 arquivos, unit + integration, 109+ testes após TSN |
| TSTR benchmark | AUC gap = 0% (LR/RF/XGBoost) — validado em dataset v4.2 |

---

## 8. Priorização dos Gaps

### Alta Prioridade

| Gap | Esforço | Impacto |
|-----|---------|---------|
| `validate_correlations.py` | 2h | Garante que os 4 padrões de fraude funcionam corretamente |
| `check_schema.py` atualizado | 3h | Regressão silenciosa em campos novos |
| `num_failed_auth_attempts` | 1h | Feature ausente para ATO detection |
| Duplicação enricher vs transaction.py | 2h | Bug latente — campos calculados em dois lugares |

### Média Prioridade

| Gap | Esforço | Impacto |
|-----|---------|---------|
| Account ramp-up (T4) | 3h | Feature realismo para novos clientes |
| AUTOFRAUDE reclassification (T7) | 1h | Distribuição de fraud types mais realista |
| Latência de fraude T1 | 4h | Padrão temporal ENGENHARIA_SOCIAL |
| TSTR re-execução pós v4.4+ | 2h | Validar que qualidade ML não regrediu |
| `brazildata_schema.json` atualizado | 2h | Fonte de verdade desatualizada |

### Baixa Prioridade (infraestrutura)

| Gap | Esforço | Impacto |
|-----|---------|---------|
| Produção ROTEIRO (Fases 1–8) | 1–2 dias | Necessário apenas para lançar produto SaaS |
| `synthfin-api` repo criar | 4h | Necessário para deploy-product workflow |
| RESUMO_EXECUTIVO atualizar/arquivar | 30min | Documentação desatualizada |
| ARCHITECTURE.md atualizar | 1h | Dois caminhos de geração não documentados |
| Redis: documentar no README | 30min | Feature existente não descobrível |

---

## 9. Checklist de Próximas Ações

```
CÓDIGO (gaps de implementação)
  [ ] Criar validate_correlations.py (ou mover para tests/unit/)
  [ ] Atualizar check_schema.py para todos os campos novos T3–TPRD3
  [ ] Implementar num_failed_auth_attempts em session_context + transaction
  [ ] Remover duplicação network_type/language_locale (enricher vs transaction.py)
  [ ] Implementar account_ramp_up em customer+transaction generators
  [ ] Mesclar AUTOFRAUDE em FRAUDE_AMIGAVEL com peso 12%
  [ ] Adicionar compromise_date + first_fraud_date para ENGENHARIA_SOCIAL/PHISHING

QUALIDADE
  [ ] Rodar validate_realism.py e confirmar geo cluster >90%
  [ ] Rodar TSTR benchmark no dataset v4.8 — verificar AUC gap <1%
  [ ] Criar tests/quality/test_data_invariants.py (smoke tests de distribuição)
  [ ] Atualizar brazildata_schema.json para v2.1 com todos os campos novos
  [ ] Atualizar rideshare_full.json com campos T5

DOCUMENTAÇÃO
  [ ] Commitar INDEX.md com links para ROTEIRO_PRODUCAO.md e GAP_ANALYSIS.md
  [ ] Arquivar RESUMO_EXECUTIVO.md em docs/analysis/archive/
  [ ] Atualizar ARCHITECTURE.md para mencionar o enricher pipeline como 2ª rota

PRODUÇÃO (quando pronto para lançar)
  [ ] Criar synthfin-api e synthfin-web repos privados
  [ ] Executar ROTEIRO_PRODUCAO.md Fases 1–8 na ordem
  [ ] Configurar Stripe webhook pós VPS
```

---

*Gerado por análise estática do código + cruzamento com TURNOS_IMPLEMENTACAO.md, RESUMO_EXECUTIVO.md e ROTEIRO_PRODUCAO.md.*
*Versão do projeto analisada: 4.8.0 (branch v4-beta, commit 0160bfd)*
