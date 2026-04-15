# synthfin-data — Documentation

Welcome to the **synthfin-data** documentation hub. This project generates realistic synthetic datasets for Brazilian banking and ride-share fraud detection.

## Where to Start

| Goal | Document |
|------|----------|
| **Get running in 2 minutes** | [README.md](../README.md) |
| **Understand the architecture** | [ARCHITECTURE.md](../ARCHITECTURE.md) |
| **See what changed** | [CHANGELOG.md](CHANGELOG.md) |
| **Browse all docs** | [INDEX.md](INDEX.md) |
| **Read in Portuguese** | [README.pt-BR.md](README.pt-BR.md) |

## Documentation Map

### Core Reference

| Document | Content |
|----------|---------|
| [01 — Visão Geral](01_VISAO_GERAL.md) | Ecosystem overview, components, metrics |
| [02 — Guia de Geração](02_GUIA_GERACAO.md) | How and why to generate data, 3 modes, 4-phase pipeline |
| [03 — Arquitetura Técnica](03_ARQUITETURA_TECNICA.md) | 5 layers, directory structure, calibration flow |
| [04 — API & RAG](04_API_RAG_REFERENCIA.md) | Endpoints, RAG internals, LLM fallback, CORS |
| [05 — Notebooks & Calibração](05_NOTEBOOKS_CALIBRACAO.md) | 8 notebooks, 14 support scripts |
| [06 — Stack Tecnológico](06_STACK_TECNOLOGICO.md) | Dependencies, Docker/Traefik, Qdrant, LLMs, tests |
| [07 — Catálogo de Fraudes](07_CATALOGO_FRAUDES.md) | 25 banking + 11 ride-share fraud types, prevalences |
| [08 — Formatos de Output](08_FORMATOS_OUTPUT.md) | 8 export formats, compression, declarative schemas |

### Deep Dives

| Area | Documents |
|------|-----------|
| **Analysis** | [analysis/](analysis/) — 11 docs covering architecture, gaps, calibration, profiles |
| **Performance** | [performance/](performance/) — capacity planning, memory optimization, multiprocessing |
| **Fraud Research** | [fraudes/](fraudes/) — 64+ patterns, validation, implementation phases |
| **Reference Data** | [documentodeestudos/](documentodeestudos/) — canonical schemas, sample payloads, TSTR benchmark |

### Technical Guides

| Document | Content |
|----------|---------|
| [GUIA_TECNICO_COMPONENTES.md](GUIA_TECNICO_COMPONENTES.md) | Component usage guide with examples |
| [DOCKER_HUB_PUBLISHING.md](DOCKER_HUB_PUBLISHING.md) | Docker Hub publishing with CI/CD |
| [ARQUITETURA.md](ARQUITETURA.md) | Architecture deep-dive (Portuguese) |

## AI Agents

The project includes 9 specialized AI agents for VS Code Copilot and Claude Code. See [AGENTS.md](../AGENTS.md) for the full routing table.

## License

Custom non-commercial license. Free for study and research. See [LICENSE](../LICENSE).
