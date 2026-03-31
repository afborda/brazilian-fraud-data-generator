# Documentation Index

## Quick Navigation

### 📋 Main Documentation
- [README](README.md) - Main project documentation (English)
- [README.pt-BR](README.pt-BR.md) - Main project documentation (Portuguese)
- [CHANGELOG](CHANGELOG.md) - Version history and release notes
- [ARQUITETURA.md](ARQUITETURA.md) - Technical architecture deep-dive (Portuguese)

> 🔒 **Docs de estratégia** (monetização, pricing, roadmap de produto, análise de concorrentes) foram movidos para o repositório privado `afborda/synthfin-saas`.

---

## � Documentação Completa do Ecossistema (FraudFlow + SynthFin)

Série de 8 documentos cobrindo todo o ecossistema — da geração de dados à API, RAG, notebooks e stack tecnológico.

| # | Documento | Conteúdo |
|---|-----------|----------|
| 01 | [Visão Geral](01_VISAO_GERAL.md) | Ecossistema, componentes, métricas V5, workflow |
| 02 | [Guia de Geração](02_GUIA_GERACAO.md) | Como e por que gerar dados, 3 modos, pipeline 4 fases |
| 03 | [Arquitetura Técnica](03_ARQUITETURA_TECNICA.md) | 5 camadas, estrutura de diretórios, fluxo de calibração |
| 04 | [API & RAG — Referência](04_API_RAG_REFERENCIA.md) | Todos os endpoints, RAG internals, LLM fallback, CORS |
| 05 | [Notebooks & Calibração](05_NOTEBOOKS_CALIBRACAO.md) | 8 notebooks detalhados, 14 scripts de suporte |
| 06 | [Stack Tecnológico](06_STACK_TECNOLOGICO.md) | Dependências, infra Docker/Traefik, Qdrant, LLMs, testes |
| 07 | [Catálogo de Fraudes](07_CATALOGO_FRAUDES.md) | 25 tipos bancários + 11 ride-share, prevalências, RAG scores |
| 08 | [Formatos de Output](08_FORMATOS_OUTPUT.md) | 8 formatos de exportação, compressão, schemas declarativos |

---

## �📚 Documentation Directories

### 📂 Documentos de Estudos Técnicos (`/documentodeestudos`)
Artefatos de referência: schema canônico, payloads de exemplo, pipelines CI/CD, benchmark TSTR.

| File | Purpose |
|------|---------|
| [brazildata_schema.json](documentodeestudos/brazildata_schema.json) | Schema JSON canônico — contrato de campos ← **fonte de verdade de campos** |
| [brazildata_entities.json](documentodeestudos/brazildata_entities.json) | Definição de entidades (Customer, Device, Transaction) |
| [brazildata_sample_payloads.json](documentodeestudos/brazildata_sample_payloads.json) | Exemplos de payload JSON para validação manual |
| [brazildata-infra-README.md](documentodeestudos/brazildata-infra-README.md) | Blueprint da VPS OVH: estrutura do repo `brazildata-infra`, 6 camadas de segurança |
| [SynthLab_CICD_Pipelines.md](documentodeestudos/SynthLab_CICD_Pipelines.md) | YAML completo dos 4 pipelines GitHub Actions (produto, site, infra, OS release) |
| [synthfin_tstr_benchmark.py](documentodeestudos/synthfin_tstr_benchmark.py) | Script TSTR: treina em sintético, testa em real — valida qualidade dos dados |
| [synthfin_tstr_results.csv](documentodeestudos/synthfin_tstr_results.csv) | Resultados TSTR: AUC gap = 0.0% (LR/RF/XGBoost) — dados passam validação ML |

### 📊 Analysis & Insights (`/analysis`)
Deep-dive analysis of project architecture, performance metrics, and behavioral patterns.

| File | Purpose |
|------|---------|
| [RESUMO_EXECUTIVO.md](analysis/RESUMO_EXECUTIVO.md) | Executive summary of project status and achievements |
| [ANALISE_PROFUNDA.md](analysis/ANALISE_PROFUNDA.md) | Deep architectural analysis |
| [ANALISE_GANHOS_E_ARQUITETURA.md](analysis/ANALISE_GANHOS_E_ARQUITETURA.md) | Gains and architecture improvements |
| [ANALISE_ECOSSISTEMA_SYNTHFIN.md](analysis/ANALISE_ECOSSISTEMA_SYNTHFIN.md) | Integrated ecosystem analysis (data + API + web + SaaS) |
| [ANALISE_GAPS_E_MELHORIAS.md](analysis/ANALISE_GAPS_E_MELHORIAS.md) | Gap analysis: critical issues, improvements |
| [ANALISE_TIERS_PAGO_GRATUITO.md](analysis/ANALISE_TIERS_PAGO_GRATUITO.md) | Free vs paid tier separation strategy |
| [METRICAS_DETALHADAS.md](analysis/METRICAS_DETALHADAS.md) | Detailed performance metrics |
| [VISUAL_SUMMARY.md](analysis/VISUAL_SUMMARY.md) | Visual project summary |
| [ESTUDO_PERFIS_COMPORTAMENTAIS.md](analysis/ESTUDO_PERFIS_COMPORTAMENTAIS.md) | Behavioral profile research |

### 🚨 Fraud Research (`/fraudes`)
Fraud taxonomy, validation analysis, and implementation roadmap.

| File | Purpose |
|------|---------|
| [INDICE_EXECUTIVO.md](fraudes/INDICE_EXECUTIVO.md) | Executive index: 64+ fraud patterns found, TOP 5 actions |
| [FRAUDES_DESCOBERTAS.md](fraudes/FRAUDES_DESCOBERTAS.md) | Deep fraud research: 50+ patterns discovered |
| [ANALISE_VALIDACAO_DADOS.md](fraudes/ANALISE_VALIDACAO_DADOS.md) | Data validation: synthetic vs. reality quality metrics |
| [MATRIZ_FRAUDES.md](fraudes/MATRIZ_FRAUDES.md) | Fraud matrix quick reference table |
| [TURNOS_IMPLEMENTACAO.md](fraudes/TURNOS_IMPLEMENTACAO.md) | Implementation shifts: 8 sequential phases |

---

## 🔧 Technical Guides

| File | Purpose |
|------|---------|
| [GUIA_TECNICO_COMPONENTES.md](GUIA_TECNICO_COMPONENTES.md) | Component usage guide with code examples |
| [ANALISE_COMPLETA_PROJETO.md](ANALISE_COMPLETA_PROJETO.md) | Comprehensive project analysis |
| [CALIBRACAO_DADOS_REAIS_BCB.md](CALIBRACAO_DADOS_REAIS_BCB.md) | BCB real data calibration reference |
| [CAPACITY_PLANNING.md](CAPACITY_PLANNING.md) | VPS capacity planning and RAM optimization |
| [MEMORY_OPTIMIZATION.md](MEMORY_OPTIMIZATION.md) | Memory optimization strategies for 50GB+ datasets |
| [MULTIPROCESSING_BENCHMARK.md](MULTIPROCESSING_BENCHMARK.md) | Streaming multiprocessing GIL bypass results |
| [DOCKER_HUB_PUBLISHING.md](DOCKER_HUB_PUBLISHING.md) | Docker Hub publishing guide with CI/CD workflow |

---

## 🎯 Quick Start Guide

### For New Developers:
1. Read [README](README.md) (5 min)
2. Check [RESUMO_EXECUTIVO.md](analysis/RESUMO_EXECUTIVO.md) (10 min)
3. Review [GUIA_TECNICO_COMPONENTES.md](GUIA_TECNICO_COMPONENTES.md) (20 min)

### For Architecture Understanding:
1. Read [ARQUITETURA.md](ARQUITETURA.md)
2. Review [ANALISE_PROFUNDA.md](analysis/ANALISE_PROFUNDA.md)
3. Check [METRICAS_DETALHADAS.md](analysis/METRICAS_DETALHADAS.md)

### For Fraud Research:
1. Read [fraudes/FRAUDES_DESCOBERTAS.md](fraudes/FRAUDES_DESCOBERTAS.md)
2. Check [fraudes/MATRIZ_FRAUDES.md](fraudes/MATRIZ_FRAUDES.md)
3. Review [fraudes/TURNOS_IMPLEMENTACAO.md](fraudes/TURNOS_IMPLEMENTACAO.md)

---

## 📊 Project Statistics

- **Total Documentation Files**: ~35
- **Ecosystem Docs (01–08)**: 8
- **Analysis Documents**: 9
- **Fraud Research Documents**: 5
- **Technical Guides**: 7

---

## Version

**Current Version**: 4.16
**Last Updated**: March 2026

See [CHANGELOG](CHANGELOG.md) for version history.
