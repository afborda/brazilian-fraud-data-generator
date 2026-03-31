# 🤖 agent-ia — Sistema Multi-Agente do synthfin-data

## Visão Geral

Este diretório contém a documentação completa de **13 agentes de IA** que orquestram o desenvolvimento, manutenção, evolução e operação do projeto synthfin-data — gerador de dados sintéticos para detecção de fraude bancária brasileira.

## Arquitetura

```
                    ┌───────────────────────────┐
                    │   00-ORQUESTRADOR (🎯)     │
                    │   ORCH-00 · Core           │
                    │   Ponto de entrada único    │
                    └─────────────┬───────────────┘
                                  │ Roteia para
              ┌───────────────────┼───────────────────┐
              │                                       │
       ┌──────▼──────┐                         ┌──────▼──────┐
       │  🆕 NOVOS   │                         │ ✅ MELHORADOS│
       │  (4 agentes)│                         │ (8 agentes)  │
       └──────┬──────┘                         └──────┬──────┘
              │                                       │
   ┌──────────┤                            ┌──────────┤
   │ 01-ANLT  Analytics              │ 03-FRAD  Fraud Engineer
   │ 02-DGEN  Data Generator         │ 04-PERF  Performance
   │ 05-DOCK  Docker & Infra         │ 06-DOCS  Documentation
   │ 08-MRKT  Market Research        │ 07-TEST  Test Coverage
   └──────────────────               │ 09-CONF  Config Architect
                                     │ 10-CICD  CI/CD Specialist
                                     │ 11-EXPL  Explorer
                                     │ 12-QUAL  Data Quality
                                     └──────────────────
```

## Índice de Agentes

| # | Código | Nome | Tipo | Status | Arquivo |
|---|--------|------|------|--------|---------|
| 0 | `ORCH-00` | **Orquestrador** | Meta-agente | ✅ Core | [00-ORQUESTRADOR.md](00-ORQUESTRADOR.md) |
| 1 | `ANLT-01` | **Analytics Agent** | Análise de dados | 🆕 Novo | [01-ANALYTICS-AGENT.md](01-ANALYTICS-AGENT.md) |
| 2 | `DGEN-02` | **Data Generator Agent** | Operação de pipeline | 🆕 Novo | [02-DATA-GENERATOR-AGENT.md](02-DATA-GENERATOR-AGENT.md) |
| 3 | `FRAD-03` | **Fraud Pattern Engineer** | Padrões de fraude | ✅ Melhorado | [03-FRAUD-PATTERN-ENGINEER.md](03-FRAUD-PATTERN-ENGINEER.md) |
| 4 | `PERF-04` | **Performance Optimizer** | Otimização | ✅ Melhorado | [04-PERFORMANCE-OPTIMIZER.md](04-PERFORMANCE-OPTIMIZER.md) |
| 5 | `DOCK-05` | **Docker & Infra Agent** | Containerização | 🆕 Novo | [05-DOCKER-INFRA-AGENT.md](05-DOCKER-INFRA-AGENT.md) |
| 6 | `DOCS-06` | **Documentation Keeper** | Governança de docs | ✅ Melhorado | [06-DOCUMENTATION-KEEPER.md](06-DOCUMENTATION-KEEPER.md) |
| 7 | `TEST-07` | **Test Coverage Agent** | Testes e cobertura | ✅ Melhorado | [07-TEST-COVERAGE-AGENT.md](07-TEST-COVERAGE-AGENT.md) |
| 8 | `MRKT-08` | **Market Research Agent** | Pesquisa de mercado | 🆕 Novo | [08-MARKET-RESEARCH-AGENT.md](08-MARKET-RESEARCH-AGENT.md) |
| 9 | `CONF-09` | **Config Architect** | Configurações | ✅ Melhorado | [09-CONFIG-ARCHITECT.md](09-CONFIG-ARCHITECT.md) |
| 10 | `CICD-10` | **CI/CD Specialist** | Pipelines CI | ✅ Melhorado | [10-CICD-SPECIALIST.md](10-CICD-SPECIALIST.md) |
| 11 | `EXPL-11` | **Explorer Agent** | Exploração (read-only) | ✅ Melhorado | [11-EXPLORER-AGENT.md](11-EXPLORER-AGENT.md) |
| 12 | `QUAL-12` | **Data Quality Analyst** | Qualidade de dados | ✅ Melhorado | [12-DATA-QUALITY-ANALYST.md](12-DATA-QUALITY-ANALYST.md) |

## Agentes Novos (4) — Por Que Foram Criados

### 🆕 Analytics Agent (`ANLT-01`)
**Gap identificado**: O projeto tinha benchmarks isolados (`data_quality_benchmark.py`, `tstr_benchmark.py`, `privacy_metrics.py`) mas nenhum agente que orquestra todos, interpreta resultados cruzados, e detecta drift entre versões.

### 🆕 Data Generator Agent (`DGEN-02`)
**Gap identificado**: Nenhum agente era responsável pelo pipeline de geração em si. Generators, entity chain, e a paridade batch/stream não tinham guardião dedicado. Mudanças em um generator podiam quebrar o pipeline sem detecção.

### 🆕 Docker & Infra Agent (`DOCK-05`)
**Gap identificado**: Docker era tratado como sub-tarefa do CI/CD, mas tem problemas próprios e urgentes: VERSION=4.9.1 no Dockerfile, label MIT errada, image name desatualizado, server sem requirements file. Precisa de agente dedicado.

### 🆕 Market Research Agent (`MRKT-08`)
**Gap identificado**: Todos os agentes olhavam para dentro (código). Nenhum olhava para fora (mercado). O projeto compete com Gretel, Mostly AI, SDV — precisa de inteligência sobre concorrentes, regulamentação BCB, e novos tipos de fraude emergentes.

## Fluxo de Trabalho Típico

### Cenário 1: "Quero melhorar a qualidade dos dados"
```
Usuário → Orquestrador
  → Quality (QUAL-12): roda benchmark, identifica score 8.0 em distribuições
  → Analytics (ANLT-01): deep dive nos campos que falham KS-test
  → Config (CONF-09): ajusta config/distributions.py
  → Quality (QUAL-12): re-valida (score subiu?)
  → Docs (DOCS-06): registra no CHANGELOG
```

### Cenário 2: "Quero adicionar novo tipo de fraude PIX"
```
Usuário → Orquestrador
  → Market (MRKT-08): pesquisa tipo de fraude PIX mais recente (BCB data)
  → Fraud (FRAD-03): cria padrão em fraud_patterns.py
  → Data Gen (DGEN-02): gera dataset com novo padrão
  → Quality (QUAL-12): valida que AUC-ROC se manteve
  → Test (TEST-07): gera testes para o novo padrão
  → Docs (DOCS-06): atualiza CHANGELOG
```

### Cenário 3: "Quero fazer deploy de nova versão"
```
Usuário → Orquestrador
  → Docs (DOCS-06): bump versão em TODOS os locais
  → Docker (DOCK-05): rebuild e publica imagem
  → CI/CD (CICD-10): verifica pipeline, quality gates
  → Quality (QUAL-12): benchmark final antes do release
```

## Estado do Projeto (Março 2026)

| Dimensão | Valor | Status |
|----------|-------|--------|
| Score Qualidade | 9.70/10 (A+) | ✅ |
| AUC-ROC | 0.9991 | ✅ |
| Distribuições | 8.0/10 | ⚠️ Ponto fraco |
| Test Coverage | ~15-20% | ❌ Crítico |
| Version Sync | 4.9.1 ≠ 4.15.1 | ❌ Drift |
| Docs Freshness | "Junho 2025" | ❌ 9 meses stale |
| Módulos Source | ~75 | — |
| Tipos de Fraude | 25 + 11 | — |
| Agentes | 13 (9 melhorados + 4 novos) | ✅ |

## Prioridades Identificadas

| # | Ação | Agente Responsável | Urgência |
|---|------|-------------------|----------|
| 1 | Corrigir version drift (4.9.1 → 4.15.1+) | DOCS-06 | 🔴 Crítica |
| 2 | Subir cobertura de testes (~15% → ≥80%) | TEST-07 | 🔴 Crítica |
| 3 | Atualizar documentação stale | DOCS-06 | 🟡 Alta |
| 4 | Corrigir Docker issues (version, label, image name) | DOCK-05 | 🟡 Alta |
| 5 | Melhorar distribuições (8.0 → 9.0+) | QUAL-12 + ANLT-01 | 🟡 Alta |
| 6 | Implementar CI quality gates | CICD-10 | 🟡 Alta |
| 7 | Pesquisar novos tipos fraude (DREX, PIX NFC) | MRKT-08 + FRAD-03 | 🟢 Média |
| 8 | Otimizar P2 (WeightCache) e P3 (OOM) | PERF-04 | 🟢 Média |

---

*Última atualização: Março 2026 | Versão: 4.15.1*
