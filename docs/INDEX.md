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
| 05 | [Notebooks & Calibração](05_NOTEBOOKS_CALIBRACAO.md) | 8 notebooks detalhados, 14 scripts de suporte |
| 06 | [Stack Tecnológico](06_STACK_TECNOLOGICO.md) | Dependências, infra Docker/Traefik, Qdrant, LLMs, testes |
| 07 | [Catálogo de Fraudes](07_CATALOGO_FRAUDES.md) | 25 tipos bancários + 11 ride-share, prevalências, RAG scores |
| 08 | [Formatos de Output](08_FORMATOS_OUTPUT.md) | 8 formatos de exportação, compressão, schemas declarativos |

---

## 📂 Subdiretórios

### 📊 Análise & Insights (`/analysis`) — 2 docs

| File | Purpose |
|------|---------|
| [ANALISE_PROFUNDA.md](analysis/ANALISE_PROFUNDA.md) | Análise arquitetural profunda |
| [ESTUDO_QUALIDADE_DADOS.md](analysis/ESTUDO_QUALIDADE_DADOS.md) | Estudo de qualidade: realismo, ML trainability, valor SaaS, score 9.08/10 |

### ⚡ Performance (`/performance`) — 2 docs

| File | Purpose |
|------|---------|
| [CAPACITY_PLANNING.md](performance/CAPACITY_PLANNING.md) | VPS capacity planning e otimização RAM (PrecomputeBuffers) |
| [MEMORY_OPTIMIZATION.md](performance/MEMORY_OPTIMIZATION.md) | Estratégias de memória para datasets 50GB+ |

### 🚨 Pesquisa de Fraude (`/fraudes`) — 0 docs ativos

Docs de planejamento/pesquisa de fraude foram consolidados no CHANGELOG após conclusão das implementações. Ver [docs/07_CATALOGO_FRAUDES.md](07_CATALOGO_FRAUDES.md) para referência atual dos 25 tipos bancários + 11 ride-share implementados.

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
2. Revisar [GUIA_TECNICO_COMPONENTES.md](GUIA_TECNICO_COMPONENTES.md) (20 min)

### Para entender a arquitetura:
1. Ler [ARQUITETURA.md](ARQUITETURA.md)
2. Revisar [ANALISE_PROFUNDA.md](analysis/ANALISE_PROFUNDA.md)

### Para pesquisa de fraude:
1. Ver [07_CATALOGO_FRAUDES.md](07_CATALOGO_FRAUDES.md) — 25 tipos bancários + 11 ride-share implementados

---

## 📊 Estatísticas

| Categoria | Quantidade |
|-----------|-----------|
| Ecosystem Docs (01–08) | 7 |
| Analysis & Insights | 2 |
| Performance | 2 |
| Fraud Research | 0 (consolidado em CHANGELOG + 07_CATALOGO_FRAUDES) |
| Technical Guides | 2 |
| Reference (estudos) | 7 (+13 PDFs) |
| **Total** | **~18 docs + 13 PDFs** |

---

## Version

**Current Version**: 4.17
**Last Updated**: April 2026

See [CHANGELOG](CHANGELOG.md) for version history.
