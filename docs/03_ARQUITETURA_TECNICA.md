# Arquitetura Técnica Completa

## Visão em Camadas

O ecossistema é composto por 5 camadas, do dado bruto ao output final:

```
┌───────────────────────────────────────────────────────────┐
│                   Camada 5: OUTPUT                        │
│  Arquivos (CSV, Parquet, JSON) | Streaming | S3 | Banco  │
└───────────────────────────────────────────────┬───────────┘
                                                │
┌───────────────────────────────────────────────┴───────────┐
│                  Camada 4: GERAÇÃO                        │
│  SynthFin-Core: CLI → Generators → Exporters → Output    │
│  Fraud injection | Profiles | Session state | Scores      │
└───────────────────────────────────────────────┬───────────┘
                                                │
┌───────────────────────────────────────────────┴───────────┐
│                  Camada 3: REGRAS                         │
│  fraud_pattern_overrides.json (25 padrões calibrados)     │
│  calibration_loader.py → FRAUD_PATTERNS mutação in-place  │
└───────────────────────────────────────────────┬───────────┘
                                                │
┌───────────────────────────────────────────────┴───────────┐
│                  Camada 2: INTELIGÊNCIA (RAG)             │
│  Qdrant (52K chunks) + LLM (Gemini/Groq/OpenAI)          │
│  Busca semântica + síntese → regras calibradas            │
└───────────────────────────────────────────────┬───────────┘
                                                │
┌───────────────────────────────────────────────┴───────────┐
│                  Camada 1: DADOS BRUTOS                   │
│  BCB | IBGE | FEBRABAN | COAF | dados.gov.br | PDFs      │
└───────────────────────────────────────────────────────────┘
```

---

## SynthFin-Core — Arquitetura Interna

### Estrutura de Diretórios

```
synthfin-core/
├── generate.py              # Entry point principal (49 linhas, dispatcher puro)
├── stream.py                # Entry point streaming (904 linhas)
├── src/fraud_generator/
│   ├── cli/                 # Interface de linha de comando
│   │   ├── args.py          # Parser de argumentos (~200 linhas)
│   │   ├── constants.py     # Constantes numéricas
│   │   ├── index_builder.py # Pré-computa índices de clientes/devices/drivers
│   │   ├── runners/         # Executores (batch, MinIO, schema)
│   │   └── workers/         # Workers para ProcessPoolExecutor
│   │
│   ├── config/              # 14 módulos de configuração estática
│   │   ├── banks.py         # Códigos BACEN, nomes, pesos de bancos
│   │   ├── calibration_loader.py  # Carrega overrides RAG
│   │   ├── devices.py       # Tipos de dispositivo, OS, browsers
│   │   ├── distributions.py # Classes de renda, distribuições salariais
│   │   ├── fraud_patterns.py # 25 definições de fraude
│   │   ├── geography.py     # 27 estados, cidades, coordenadas
│   │   ├── merchants.py     # MCCs, nomes de merchants
│   │   ├── municipios.py    # 5.570 municípios com CEPs
│   │   ├── pix.py           # Chaves PIX, campos BACEN
│   │   ├── rideshare.py     # Apps, categorias, tarifas
│   │   ├── seasonality.py   # Pesos temporais (hora/dia/mês)
│   │   ├── transactions.py  # Tipos, canais, faixas de valor
│   │   └── weather.py       # Condições por região
│   │
│   ├── generators/          # Geradores de entidades
│   │   ├── customer.py      # CPF válido, Faker pt-BR, endereços
│   │   ├── device.py        # OS, modelos, fingerprints
│   │   ├── driver.py        # CNH, veículos, apps
│   │   ├── ride.py          # Haversine, surge pricing, fraude
│   │   ├── transaction.py   # 594 linhas, gerador principal (117 campos)
│   │   ├── score.py         # 17 sinais de risco + 4 regras de correlação
│   │   ├── correlations.py  # Pattern matching de fraude
│   │   └── session_context.py # Contexto de sessão para regras
│   │
│   ├── models/              # Dataclasses
│   │   ├── customer.py      # Customer + Address
│   │   ├── device.py        # Device
│   │   ├── ride.py          # Ride + Driver + Location
│   │   └── transaction.py   # Transaction
│   │
│   ├── profiles/            # Perfis comportamentais
│   │   ├── behavioral.py    # 7 perfis transacionais
│   │   ├── device.py        # Perfil de dispositivo
│   │   └── ride_behavioral.py # 7 perfis ride-share
│   │
│   ├── exporters/           # Exportadores (Strategy Pattern)
│   │   ├── csv_exporter.py
│   │   ├── json_exporter.py
│   │   ├── parquet_exporter.py
│   │   ├── arrow_ipc_exporter.py
│   │   ├── database_exporter.py
│   │   └── minio_exporter.py
│   │
│   ├── connections/         # Streaming connections
│   │   ├── kafka_connection.py
│   │   ├── webhook_connection.py
│   │   └── stdout_connection.py
│   │
│   ├── schema/              # Schema engine declarativo
│   │   ├── parser.py        # Valida schema vs FIELD_CATALOG
│   │   ├── mapper.py        # Resolve dot-paths para valores
│   │   ├── engine.py        # Orquestra geração por schema
│   │   └── ai_corrector.py  # Correção de schema via LLM
│   │
│   ├── utils/               # Utilitários
│   │   ├── compression.py   # gzip, zstd, snappy
│   │   ├── helpers.py       # IPs, hashing, weighted choice
│   │   ├── parallel.py      # Async stream manager
│   │   ├── precompute.py    # Buffers pré-computados (RAM)
│   │   ├── streaming.py     # Índices, SessionState, Progress
│   │   └── weight_cache.py  # LRU cache para random.choices
│   │
│   └── validators/
│       └── cpf.py           # 257 linhas: geração e validação de CPF
```

### Fluxo de Execução (Batch)

```
generate.py
    │
    ├─→ args.py (parse CLI arguments)
    ├─→ calibration_loader.py (load overrides → mutate FRAUD_PATTERNS)
    ├─→ index_builder.py (pre-compute customer/device indexes)
    │
    └─→ BatchRunner (4 phases)
         │
         ├─ Phase 1: CustomerGenerator + DeviceGenerator (sequential)
         │     ├─ CPF válido por estado (validators/cpf.py)
         │     ├─ Faker pt-BR (nome, endereço)
         │     ├─ Perfil comportamental sticky (profiles/behavioral.py)
         │     └─ Dispositivo + fingerprint (generators/device.py)
         │
         ├─ Phase 2: TransactionGenerator (ProcessPoolExecutor)
         │     ├─ Tipo de transação (PIX/CREDIT_CARD/TED/DOC/BOLETO)
         │     ├─ Canal (MOBILE_APP/WEB_BANKING/ATM/BRANCH)
         │     ├─ Merchant + MCC
         │     ├─ Valor baseado em perfil + distribuição
         │     ├─ Campos PIX BACEN (se PIX)
         │     ├─ Injeção de fraude (25 tipos)
         │     ├─ Score de risco (17 sinais + 4 correlações)
         │     └─ Geolocalização + session state
         │
         ├─ Phase 3: DriverGenerator (sequential, se rides)
         │     ├─ CNH válida com categoria
         │     ├─ Veículo + placa Mercosul
         │     └─ Apps ativos (Uber, 99, etc.)
         │
         └─ Phase 4: RideGenerator (ProcessPoolExecutor, se rides)
               ├─ Origem/destino com POIs reais
               ├─ Distância Haversine (grande círculo)
               ├─ Tarifa: base + distância + duração + surge
               ├─ Injeção de fraude (11 tipos)
               └─ Score de risco
```

---

## FraudFlow — Arquitetura Interna

### Estrutura de Diretórios

```
fraudflow/
├── docker-compose.yml       # 3 services: Qdrant + API + Jupyter
├── api/
│   ├── main.py              # FastAPI app + CORS + routers
│   ├── config.py            # Settings (Pydantic BaseSettings)
│   ├── llm_client.py        # LLM unificado (Gemini → Groq → OpenAI)
│   ├── Dockerfile           # Python 3.11 + embedding model
│   ├── requirements.txt     # Dependências
│   │
│   ├── routers/
│   │   ├── coleta.py        # Endpoints de coleta de dados
│   │   ├── rag.py           # Endpoints de busca semântica + LLM
│   │   ├── regras.py        # Geração de regras de fraude
│   │   └── lgpd.py          # Endpoints de compliance LGPD
│   │
│   ├── collectors/
│   │   ├── bacen_sgs.py     # BCB SGS + Olinda (Pix)
│   │   ├── ibge_sidra.py    # IBGE SIDRA v3 + BrasilAPI
│   │   ├── dados_gov.py     # dados.gov.br CKAN
│   │   ├── cep_localizacao.py # BrasilAPI + ViaCEP
│   │   ├── febraban_pdf.py  # PDFs FEBRABAN + COAF
│   │   └── local_dados.py   # Extração de arquivos locais
│   │
│   ├── indexer/
│   │   └── qdrant_indexer.py # Chunking + embedding + upsert
│   │
│   └── dados/               # Dados brutos (PDFs, CSVs, ZIPs)
│
├── data/
│   ├── bacen/               # Séries temporais BCB
│   ├── ibge/                # Municípios + população
│   ├── ceps/                # CEPs reais com GPS
│   ├── febraban/            # Relatórios FEBRABAN
│   ├── coaf/                # Relatórios COAF
│   ├── dados_gov/           # Datasets dados.gov.br
│   └── rules/
│       └── fraud_pattern_overrides.json  ← ARQUIVO CRÍTICO
│
├── notebooks/               # 8 notebooks de calibração
│   ├── 01_extracao_dados.ipynb
│   ├── 02_popular_rag.ipynb
│   ├── 03_gerar_regras.ipynb
│   ├── 04_calibrar_regras_synthfin.ipynb
│   ├── 05_analise_cruzada.ipynb
│   ├── 06_padroes_avancados.ipynb
│   ├── 07_validacao_calibracao_final.ipynb
│   └── 08_golpebr_analise_rag.ipynb
│
└── scripts/                 # 14 scripts de utilidade
```

### Pipeline de Dados

```
Collectors (6 fontes)
    │
    ├─→ bacen_sgs.py    → BCB SGS API (IPCA, CDI, SELIC, inadimplência)
    ├─→ ibge_sidra.py   → IBGE SIDRA v3 (população por UF)
    ├─→ dados_gov.py    → dados.gov.br CKAN (datasets abertos)
    ├─→ cep_localizacao.py → BrasilAPI + ViaCEP (CEPs + GPS)
    ├─→ febraban_pdf.py → PDFs FEBRABAN + COAF (extração pdfplumber)
    └─→ local_dados.py  → Arquivos locais (PDF, CSV, XLSX, PPTX, ZIP)
         │
         ▼
    Indexer (qdrant_indexer.py)
    ├─→ Chunking: 500 chars, 80 overlap
    ├─→ Embedding: paraphrase-multilingual-MiniLM-L12-v2 (384d)
    └─→ Upsert: Qdrant collection "fraudflow-brasil"
         │
         ▼
    RAG Query (rag.py)
    ├─→ Busca semântica (cosine similarity)
    ├─→ Top-K documentos relevantes
    └─→ Síntese por LLM (Gemini/Groq/OpenAI)
         │
         ▼
    Regras (regras.py)
    ├─→ Diagnóstico de padrões
    ├─→ Regras sugeridas
    └─→ Código Python para calibração
         │
         ▼
    fraud_pattern_overrides.json
    ├─→ 25 padrões de fraude calibrados
    ├─→ Prevalências baseadas em dados reais
    └─→ Multiplicadores e scores ajustados
```

---

## Fluxo de Calibração (fraud_pattern_overrides.json)

O arquivo mais importante do sistema. Define como cada tipo de fraude se comporta no gerador.

```
fraud_pattern_overrides.json
    │
    └─→ calibration_loader.py (synthfin-core)
         │
         ├─→ Carrega JSON de overrides
         ├─→ Para cada tipo de fraude:
         │     ├─ prevalence → FRAUD_PATTERNS[tipo]['prevalence']
         │     ├─ amount_multiplier → characteristics['amount_multiplier']
         │     ├─ fraud_score_base → characteristics['fraud_score_base']
         │     ├─ pareto_shape → characteristics['pareto_shape']
         │     └─ pareto_scale → characteristics['pareto_scale']
         │
         └─→ FRAUD_TYPES_WEIGHTS normalizado (soma = 1.0)
```

### Resolução de Caminho

O `calibration_loader.py` busca o arquivo nesta ordem:

1. Variável de ambiente `$CALIBRATION_OVERRIDES_PATH`
2. `<fraudflow_root>/data/rules/fraud_pattern_overrides.json`
3. Fallback para valores hardcoded (sem calibração)

---

## Sistema de Score de Fraude

O `generators/score.py` calcula o risco de cada transação usando:

### 17 Sinais de Risco

| # | Sinal | Peso |
|---|-------|------|
| 1 | Valor anormal para perfil | Alto |
| 2 | Horário incomum (madrugada) | Médio |
| 3 | Device não confiável | Alto |
| 4 | Velocidade de transações | Alto |
| 5 | Acúmulo em 24h | Alto |
| 6 | Localização incomum | Médio |
| 7 | Beneficiário novo | Médio |
| 8 | Tipo de transação incomum | Baixo |
| 9 | Canal incomum | Baixo |
| 10 | IP diferente | Médio |
| 11 | Merchant de risco | Médio |
| 12 | Primeira transação | Baixo |
| 13 | Conta recente | Médio |
| 14 | Valor redondo | Baixo |
| 15 | Múltiplos destinatários | Alto |
| 16 | Cross-border | Alto |
| 17 | Session duration anormal | Médio |

### 4 Regras de Correlação

1. **Burst + novo device** → Score +15%
2. **Valor alto + beneficiário novo + madrugada** → Score +20%
3. **Velocidade alta + localização diferente** → Score +18%
4. **Device não confiável + IP novo + canal web** → Score +12%

---

## Perfis Comportamentais

### 7 Perfis Transacionais

Cada cliente recebe um perfil sticky na criação. O perfil influencia:
- Faixa de valor típica
- Horários preferidos
- Canais utilizados
- Frequência de transações

| Perfil | Características |
|--------|----------------|
| SALARY_WORKER | Transações regulares, valores médios, horário comercial |
| HIGH_INCOME | Valores altos, múltiplos canais, investimentos |
| STUDENT | Valores baixos, PIX frequente, mobile dominante |
| RETIREE | Valores médios, branch frequente, horário matutino |
| SMALL_BUSINESS | Volume alto, TED/DOC, valores variados |
| FREELANCER | Irregular, PIX recebimentos, valores variados |
| LOW_INCOME | Valores baixos, poucas transações, boleto |

### 7 Perfis Ride-Share

| Perfil | Características |
|--------|----------------|
| FREQUENT_COMMUTER | Diário, mesmos horários, mesma rota |
| NIGHT_OWL | Madrugada, bares/entretenimento |
| WEEKEND_USER | Fins de semana, lazer |
| BUSINESS_TRAVELER | Aeroporto, hotel, horário comercial |
| STUDENT_RIDER | Campus, transporte público misto |
| RARE_USER | Esporádico, sem padrão |
| LUXURY_USER | Categorias premium, gorjeta alta |

---

## Infraestrutura Docker

### Serviços

```yaml
# 3 containers orquestrados
services:
  fraudflow-qdrant:      # Qdrant v1.9.2 (vector store)
    ports: 6333, 6334    # REST + gRPC

  fraudflow-data-api:    # FastAPI (Python 3.11)
    port: 8000           # API REST
    networks: default + traefik-network

  fraudflow-jupyter:     # JupyterLab (scipy-notebook)
    port: 8888           # Notebooks interativos
```

### Rede

```
Internet
    │
    ▼
Traefik (Let's Encrypt SSL)
    │
    ├─→ fraudflow.abnerfonseca.com.br → fraudflow-data-api:8000
    │
    └─→ Outros subdomínios → Outros serviços
```

### Volumes

| Volume | Conteúdo |
|--------|----------|
| `qdrant-storage` | Vetores e índices do Qdrant |
| `./data` | Dados processados e regras de calibração |
| `./api/dados` | Dados brutos (PDFs, CSVs, ZIPs) |
| `./notebooks` | Notebooks Jupyter |
| `./scripts` | Scripts de análise |
