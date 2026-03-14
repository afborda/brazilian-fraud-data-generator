# Documentation Index

## Quick Navigation

### 📋 Main Documentation
- [README](README.md) - Main project documentation (English)
- [README.pt-BR](README.pt-BR.md) - Main project documentation (Portuguese)
- [CHANGELOG](CHANGELOG.md) - Version history and release notes
- [ARQUITETURA.md](ARQUITETURA.md) - Technical architecture deep-dive (Portuguese)

> 🔒 **Docs de estratégia** (monetização, pricing, roadmap de produto, análise de concorrentes) foram movidos para o repositório privado `afborda/synthfin-saas`.

---

## 📚 Documentation Directories

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
| [ANALISE_PC.md](analysis/ANALISE_PC.md) | Performance characteristics analysis |
| [ANALISE_GANHOS_E_ARQUITETURA.md](analysis/ANALISE_GANHOS_E_ARQUITETURA.md) | Gains and architecture improvements |
| [METRICAS_DETALHADAS.md](analysis/METRICAS_DETALHADAS.md) | Detailed performance metrics |
| [VISUAL_SUMMARY.md](analysis/VISUAL_SUMMARY.md) | Visual project summary |
| [ESTUDO_PERFIS_COMPORTAMENTAIS.md](analysis/ESTUDO_PERFIS_COMPORTAMENTAIS.md) | Behavioral profile research |
| [INDICE_ANALISE.md](analysis/INDICE_ANALISE.md) | Analysis index |

### 🚨 Fraud Research (`/fraudes`)
Fraud taxonomy, validation analysis, and implementation roadmap.

| File | Purpose |
|------|---------|
| [README.md](fraudes/README.md) | Fraud documentation index |
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
| [MEMORY_OPTIMIZATION.md](MEMORY_OPTIMIZATION.md) | Memory optimization strategies for 50GB+ datasets |
| [CAPACITY_PLANNING.md](CAPACITY_PLANNING.md) | VPS sizing and throughput estimation |
| [MULTIPROCESSING_BENCHMARK.md](MULTIPROCESSING_BENCHMARK.md) | Streaming multiprocessing GIL bypass results |
| [DOCKER_HUB_PUBLISHING.md](DOCKER_HUB_PUBLISHING.md) | Docker Hub publishing guide with CI/CD workflow |
| [REPOSITORY_ORGANIZATION.md](REPOSITORY_ORGANIZATION.md) | Repository structure and git workflow guide |

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

- **Total Documentation Files**: ~30
- **Analysis Documents**: 8
- **Fraud Research Documents**: 6
- **Technical Guides**: 7

---

## Version

**Current Version**: 4.5.0  
**Last Updated**: March 14, 2026

See [CHANGELOG](CHANGELOG.md) for version history.
