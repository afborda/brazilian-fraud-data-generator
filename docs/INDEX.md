# Documentation Index

## Quick Navigation

### 📋 Main Documentation
- [README](README.md) — Documentation hub (English)
- [README.pt-BR](README.pt-BR.md) — Main project documentation (Portuguese)
- [CHANGELOG](CHANGELOG.md) — Version history and release notes
- [ARQUITETURA.md](ARQUITETURA.md) — Technical architecture deep-dive (Portuguese)
- [AGENTS.md](../AGENTS.md) — AI agent registry and routing table

> 🔒 **Docs de estratégia** (monetização, pricing, roadmap de produto, análise de concorrentes) foram movidos para o repositório privado `afborda/synthfin-saas`.

---

## 📖 Documentação do Ecossistema (01–08)

Série de 8 documentos cobrindo todo o ecossistema — da geração de dados à API, RAG, notebooks e stack tecnológico.

| # | Documento | Conteúdo |
|---|-----------|----------|
| 01 | [Visão Geral](01_VISAO_GERAL.md) | Ecossistema, componentes, métricas, workflow |
| 02 | [Guia de Geração](02_GUIA_GERACAO.md) | Como e por que gerar dados, 3 modos, pipeline 4 fases |
| 03 | [Arquitetura Técnica](03_ARQUITETURA_TECNICA.md) | 5 camadas, estrutura de diretórios, fluxo de calibração |
| 04 | [API & RAG — Referência](04_API_RAG_REFERENCIA.md) | Todos os endpoints, RAG internals, LLM fallback, CORS |
| 05 | [Notebooks & Calibração](05_NOTEBOOKS_CALIBRACAO.md) | 8 notebooks detalhados, 14 scripts de suporte |
| 06 | [Stack Tecnológico](06_STACK_TECNOLOGICO.md) | Dependências, infra Docker/Traefik, Qdrant, LLMs, testes |
| 07 | [Catálogo de Fraudes](07_CATALOGO_FRAUDES.md) | 25 tipos bancários + 11 ride-share, prevalências, RAG scores |
| 08 | [Formatos de Output](08_FORMATOS_OUTPUT.md) | 8 formatos de exportação, compressão, schemas declarativos |

---

## 📂 Subdiretórios

### 📊 Análise & Insights (`/analysis`) — 11 docs

| File | Purpose |
|------|---------|
| [RESUMO_EXECUTIVO.md](analysis/RESUMO_EXECUTIVO.md) | Resumo executivo do projeto |
| [ANALISE_PROFUNDA.md](analysis/ANALISE_PROFUNDA.md) | Análise arquitetural profunda |
| [ANALISE_COMPLETA_PROJETO.md](analysis/ANALISE_COMPLETA_PROJETO.md) | Análise completa do projeto (75+ módulos) |
| [ANALISE_GANHOS_E_ARQUITETURA.md](analysis/ANALISE_GANHOS_E_ARQUITETURA.md) | Ganhos de performance e melhorias SOLID |
| [ANALISE_ECOSSISTEMA_SYNTHFIN.md](analysis/ANALISE_ECOSSISTEMA_SYNTHFIN.md) | Ecossistema integrado (data + API + web + SaaS) |
| [ANALISE_GAPS_E_MELHORIAS.md](analysis/ANALISE_GAPS_E_MELHORIAS.md) | Gaps, erros e melhorias identificados |
| [ANALISE_TIERS_PAGO_GRATUITO.md](analysis/ANALISE_TIERS_PAGO_GRATUITO.md) | Estratégia de separação free vs paid |
| [CALIBRACAO_DADOS_REAIS_BCB.md](analysis/CALIBRACAO_DADOS_REAIS_BCB.md) | Calibração com dados reais BCB + RAG |
| [METRICAS_DETALHADAS.md](analysis/METRICAS_DETALHADAS.md) | Métricas detalhadas de performance |
| [VISUAL_SUMMARY.md](analysis/VISUAL_SUMMARY.md) | Resumo visual do projeto |
| [ESTUDO_PERFIS_COMPORTAMENTAIS.md](analysis/ESTUDO_PERFIS_COMPORTAMENTAIS.md) | Pesquisa de perfis comportamentais |

### ⚡ Performance (`/performance`) — 3 docs

| File | Purpose |
|------|---------|
| [CAPACITY_PLANNING.md](performance/CAPACITY_PLANNING.md) | VPS capacity planning e otimização RAM |
| [MEMORY_OPTIMIZATION.md](performance/MEMORY_OPTIMIZATION.md) | Estratégias de memória para datasets 50GB+ |
| [MULTIPROCESSING_BENCHMARK.md](performance/MULTIPROCESSING_BENCHMARK.md) | Benchmark multiprocessing GIL bypass |

### 🚨 Pesquisa de Fraude (`/fraudes`) — 5 docs

| File | Purpose |
|------|---------|
| [INDICE_EXECUTIVO.md](fraudes/INDICE_EXECUTIVO.md) | Índice executivo: 64+ padrões, TOP 5 ações |
| [FRAUDES_DESCOBERTAS.md](fraudes/FRAUDES_DESCOBERTAS.md) | Pesquisa profunda: 50+ padrões descobertos |
| [ANALISE_VALIDACAO_DADOS.md](fraudes/ANALISE_VALIDACAO_DADOS.md) | Validação: sintético vs. realidade |
| [MATRIZ_FRAUDES.md](fraudes/MATRIZ_FRAUDES.md) | Matriz de fraudes — referência rápida |
| [TURNOS_IMPLEMENTACAO.md](fraudes/TURNOS_IMPLEMENTACAO.md) | Turnos de implementação: 8 fases |

### 📚 Documentos de Estudos (`/documentodeestudos`) — referência

| File | Purpose |
|------|---------|
| [brazildata_schema.json](documentodeestudos/brazildata_schema.json) | Schema JSON canônico — **fonte de verdade** |
| [brazildata_entities.json](documentodeestudos/brazildata_entities.json) | Definição de entidades (Customer, Device, Transaction) |
| [brazildata_sample_payloads.json](documentodeestudos/brazildata_sample_payloads.json) | Exemplos de payload JSON |
| [brazildata-infra-README.md](documentodeestudos/brazildata-infra-README.md) | Blueprint da VPS OVH |
| [SynthLab_CICD_Pipelines.md](documentodeestudos/SynthLab_CICD_Pipelines.md) | YAML dos 4 pipelines GitHub Actions |
| [synthfin_tstr_benchmark.py](documentodeestudos/synthfin_tstr_benchmark.py) | Script TSTR: treina em sintético, testa em real |
| [synthfin_tstr_results.csv](documentodeestudos/synthfin_tstr_results.csv) | Resultados TSTR: AUC gap = 0.0% |

---

## 🔧 Guias Técnicos (raiz do docs/)

| File | Purpose |
|------|---------|
| [GUIA_TECNICO_COMPONENTES.md](GUIA_TECNICO_COMPONENTES.md) | Guia de uso de cada componente com exemplos |
| [DOCKER_HUB_PUBLISHING.md](DOCKER_HUB_PUBLISHING.md) | Publicação no Docker Hub com CI/CD |

### 🛠️ Utility Scripts (`/tools`)

| File | Purpose |
|------|---------|
| [backtest_rules.py](../tools/backtest_rules.py) | Backtesting de regras de fraude contra dataset existente |
| [tstr_benchmark.py](../tools/tstr_benchmark.py) | Train Synthetic, Test Real (RF + XGBoost) |
| [privacy_metrics.py](../tools/privacy_metrics.py) | Métricas de privacidade LGPD |
| [qde_filter.py](../tools/qde_filter.py) | Quality Data Extractor — filtra inconsistências |
| [validate/dashboard.py](../tools/validate/dashboard.py) | Dashboard interativo Streamlit para validação |

---

## 🎯 Quick Start Guide

### Para novos desenvolvedores:
1. Ler [README](README.md) (5 min)
2. Ver [RESUMO_EXECUTIVO.md](analysis/RESUMO_EXECUTIVO.md) (10 min)
3. Revisar [GUIA_TECNICO_COMPONENTES.md](GUIA_TECNICO_COMPONENTES.md) (20 min)

### Para entender a arquitetura:
1. Ler [ARQUITETURA.md](ARQUITETURA.md)
2. Revisar [ANALISE_PROFUNDA.md](analysis/ANALISE_PROFUNDA.md)
3. Conferir [METRICAS_DETALHADAS.md](analysis/METRICAS_DETALHADAS.md)

### Para pesquisa de fraude:
1. Ler [FRAUDES_DESCOBERTAS.md](fraudes/FRAUDES_DESCOBERTAS.md)
2. Ver [MATRIZ_FRAUDES.md](fraudes/MATRIZ_FRAUDES.md)
3. Revisar [TURNOS_IMPLEMENTACAO.md](fraudes/TURNOS_IMPLEMENTACAO.md)

---

## 📊 Estatísticas

| Categoria | Quantidade |
|-----------|-----------|
| Ecosystem Docs (01–08) | 8 |
| Analysis & Insights | 11 |
| Performance | 3 |
| Fraud Research | 5 |
| Technical Guides | 2 |
| Reference (estudos) | 7 (+13 PDFs) |
| **Total** | **~36 docs + 13 PDFs** |

---

## Version

**Current Version**: 4.17
**Last Updated**: April 2026

See [CHANGELOG](CHANGELOG.md) for version history.
