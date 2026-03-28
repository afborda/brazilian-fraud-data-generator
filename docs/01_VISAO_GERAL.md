# SynthFin + FraudFlow — Visão Geral do Ecossistema

## O que é

O **SynthFin** é um gerador de dados financeiros sintéticos realistas, focado no mercado brasileiro. Ele produz transações bancárias e corridas de ride-share com padrões de fraude calibrados por dados reais do Banco Central, IBGE, FEBRABAN e outras fontes públicas.

O **FraudFlow** é o pipeline de calibração e inteligência que alimenta o SynthFin. Ele coleta dados públicos reais, indexa em uma base de conhecimento vetorial (RAG), e usa LLMs para gerar regras de fraude calibradas que são aplicadas ao gerador.

Juntos, formam um ecossistema completo para geração de dados sintéticos de alta fidelidade para uso em:

- **Machine Learning** — Treino e validação de modelos anti-fraude
- **Testes de sistemas** — Dados realistas para QA de sistemas bancários
- **Compliance** — Validação de regras de detecção sem expor dados reais
- **Pesquisa acadêmica** — Datasets reprodutíveis com seed determinístico

---

## Arquitetura do Ecossistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRAUDFLOW                                │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────────┐  │
│  │Collectors│──▶│ Indexer   │──▶│   RAG    │──▶│  Regras    │  │
│  │ BCB/IBGE │   │ Qdrant   │   │ Busca    │   │ Calibradas │  │
│  │ FEBRABAN │   │ 52K+     │   │ Semântica│   │            │  │
│  │ COAF     │   │ chunks   │   │ + LLM    │   │            │  │
│  └──────────┘   └──────────┘   └──────────┘   └─────┬──────┘  │
│                                                       │         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐         │         │
│  │Notebooks │   │ Scripts  │   │   API    │         │         │
│  │ 01 a 08  │   │ Análise  │   │ FastAPI  │         │         │
│  └──────────┘   └──────────┘   └──────────┘         │         │
└──────────────────────────────────────────────────────┼─────────┘
                                                       │
                                                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                       SYNTHFIN-CORE                             │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────────┐  │
│  │Calibração│──▶│Generators│──▶│Exporters │──▶│  Output    │  │
│  │ Loader   │   │ Customer │   │ CSV/JSON │   │ Arquivos   │  │
│  │ Overrides│   │ Transação│   │ Parquet  │   │ Streaming  │  │
│  │          │   │ Ride     │   │ Arrow    │   │ Banco      │  │
│  └──────────┘   └──────────┘   └──────────┘   └────────────┘  │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                   │
│  │  Schema  │   │ Profiles │   │Validators│                   │
│  │ Engine   │   │ 7+7 tipos│   │ CPF/Score│                   │
│  └──────────┘   └──────────┘   └──────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Números da Versão Atual (v4.9.1 / V5 Calibrado)

| Métrica | Valor |
|---------|-------|
| Transações geradas | 268.435 |
| Fraudes detectadas | 2.656 (0,99%) |
| Tipos de fraude bancária | 25 |
| Tipos de fraude ride-share | 11 |
| Colunas por transação | 117 |
| Estados cobertos | 27 (todos) |
| SP + RJ + MG | 38,2% do volume |
| Ratio fraude/legítima | 5,09× |
| Score de realismo | 8,0/10 |
| Chunks no RAG | 52.547 |
| Fontes indexadas | 66 |
| Score médio RAG | 0,807 |
| Testes passando | 194 |

---

## Componentes do Ecossistema

### 1. SynthFin-Core (Gerador)

O coração do sistema. Gera dados sintéticos em múltiplos formatos com fraude calibrada.

| Módulo | Função |
|--------|--------|
| **CLI** | Interface de linha de comando com 3 modos (batch, MinIO, schema) |
| **Generators** | Geração de clientes, dispositivos, transações e corridas |
| **Exporters** | Exportação em 8 formatos (CSV, JSON, Parquet, Arrow, etc.) |
| **Connections** | Streaming para Kafka, webhooks ou stdout |
| **Config** | 14 módulos de configuração (bancos, geografia, fraudes, etc.) |
| **Schema Engine** | Geração declarativa via JSON schema |
| **Validators** | Validação de CPF, score de fraude, schema de output |
| **Profiles** | 7 perfis transacionais + 7 perfis de ride-share |

### 2. FraudFlow (Pipeline de Calibração)

Pipeline de dados que alimenta o SynthFin com informações reais.

| Módulo | Função |
|--------|--------|
| **API** | FastAPI com 15+ endpoints (coleta, RAG, regras, LGPD) |
| **Collectors** | 6 coletores de dados públicos (BCB, IBGE, FEBRABAN, etc.) |
| **Indexer** | Chunking + embedding + upsert no Qdrant |
| **RAG** | Busca semântica + síntese por LLM |
| **Notebooks** | 8 notebooks de análise e calibração |
| **Scripts** | 14 scripts de utilidade |

### 3. Infraestrutura

| Serviço | Função |
|---------|--------|
| **Qdrant** | Vector store para RAG (52K+ chunks) |
| **FastAPI** | API REST com CORS e rate limiting |
| **JupyterLab** | Análise interativa na VPS |
| **Traefik** | Reverse proxy com Let's Encrypt SSL |
| **Docker Compose** | Orquestração de 3 containers |

---

## Fluxo de Trabalho

```
1. COLETA     → Collectors buscam dados públicos (BCB, IBGE, FEBRABAN, COAF)
2. INDEXAÇÃO  → Dados são chunked, embedded e indexados no Qdrant
3. ANÁLISE    → RAG + LLM analisam padrões de fraude reais
4. REGRAS     → fraud_pattern_overrides.json é gerado/atualizado
5. GERAÇÃO    → SynthFin-Core gera dados com regras calibradas
6. VALIDAÇÃO  → Scripts verificam realismo (score, ratio, distribuição)
7. EXPORTAÇÃO → Dados exportados em formato escolhido
```

---

## Repositórios

| Repositório | Branch | Descrição |
|-------------|--------|-----------|
| `fraudflow/` | `master` | Pipeline de calibração, API, RAG, notebooks |
| `synthfin-core/` | `v4-beta` | Gerador de transações sintéticas |

---

## Próximos Passos

Consultar os demais documentos desta pasta para guias detalhados:

- [02 — Guia de Geração de Dados](02_GUIA_GERACAO.md)
- [03 — Arquitetura Técnica Completa](03_ARQUITETURA_TECNICA.md)
- [04 — API e RAG — Referência](04_API_RAG_REFERENCIA.md)
- [05 — Notebooks e Workflow de Calibração](05_NOTEBOOKS_CALIBRACAO.md)
- [06 — Stack Tecnológico](06_STACK_TECNOLOGICO.md)
- [07 — Catálogo de Fraudes](07_CATALOGO_FRAUDES.md)
- [08 — Formatos de Output e Schemas](08_FORMATOS_OUTPUT.md)
