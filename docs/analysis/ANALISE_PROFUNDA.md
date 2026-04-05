# Análise Profunda - synthfin-data v4.17

## 📋 Sumário Executivo

O projeto é um **gerador de dados sintéticos de fraude brasileira** otimizado para produção. Cria transações financeiras realistas (PIX, cartão de crédito, etc.) e dados de corridas (Uber, 99, etc.) com padrões comportamentais, injeção de fraude via pipeline de 8 enrichers, e múltiplos formatos de exportação (JSONL, CSV, Parquet, MinIO/S3).

**Stack:**
- Python 3.10+
- Multiprocessing / Concurrent.futures (paralelismo)
- Faker (geração de dados)
- Pandas / PyArrow (processamento)
- boto3 (integração MinIO/S3)

---

## 🏗️ Arquitetura Geral

```
generate.py (orquestrador principal)
├── Phase 1: Gerar clientes + dispositivos (sequential)
├── Phase 2: Gerar transações (paralelo: ProcessPool/ThreadPool)
├── Phase 3: Gerar motoristas (sequential)
├── Phase 4: Gerar corridas (paralelo: ProcessPool/ThreadPool)
└── Phase 5: Agregar estatísticas
```

### Componentes Principais

```
src/fraud_generator/
├── generators/          # Gera dados sintéticos
│   ├── customer.py      # Clientes com CPF, perfil, renda
│   ├── device.py        # Dispositivos associados
│   ├── transaction.py   # Transações (PIX, cartão, etc) + pipeline enrichers
│   ├── ride.py          # Corridas de ride-share
│   ├── score.py         # fraud_risk_score (17 sinais, 0-100)
│   └── correlations.py  # 4 regras de correlação → match_fraud_rule()
├── enrichers/           # Pipeline de 8 estágios (ORDEM CRÍTICA)
│   ├── temporal.py      # 1. unusual_time flag
│   ├── geo.py           # 2. lat/lon, distância
│   ├── fraud.py         # 3. overrides de amount/location/device/channel
│   ├── pix.py           # 4. campos BACEN pacs.008
│   ├── device.py        # 5. sinais de device (emulator, rooted, new)
│   ├── session.py       # 6. velocity 24h, merchant novelty, impossible travel
│   ├── risk.py          # 7. fraud_risk_score + ring TPRD2
│   └── biometric.py     # 8. biometria (license-gated)
├── models/              # Dataclasses das entidades
│   ├── customer.py
│   ├── device.py
│   ├── transaction.py
│   └── ride.py
├── exporters/           # Múltiplos formatos de saída
│   ├── base.py          # Interface abstrata
│   ├── json_exporter.py # JSONL (streaming)
│   ├── csv_exporter.py  # CSV
│   ├── parquet_exporter.py # Parquet (comprimido)
│   └── minio_exporter.py # Upload para MinIO/S3
├── config/              # Dados configuráveis (não mudam)
│   ├── banks.py         # Bancos brasileiros
│   ├── geography.py     # Estados, cidades
│   ├── merchants.py     # MCCs, nomes de loja
│   ├── devices.py       # Tipos de dispositivo
│   └── transactions.py  # Tipos de transação, fraude, canais
├── profiles/            # Perfis comportamentais
│   └── behavioral.py    # 7 tipos: young_digital, business_owner, etc
├── utils/               # Utilitários
│   ├── helpers.py       # Parse size, IP Brazil, hashing
│   ├── streaming.py     # CustomerIndex, DeviceIndex (leve)
│   └── validators/      # Validação CPF
└── validators/
    └── cpf.py          # CPF validate + generate
```

---

## 🔍 Análise Funcional Detalhada

### 1️⃣ **GERAÇÃO DE CLIENTES** (`generate_customers_and_devices()`)

**Entrada:** `num_customers=10000, use_profiles=True, seed=42`

**Processo:**
1. Para cada cliente i:
   - Atribui **perfil comportamental aleatório** (ex: `young_digital`)
   - Gera **CPF válido** (com dígitos verificadores corretos, respeitando estado)
   - Atribui **data de nascimento** baseada no perfil (ex: senior: 65-80 anos)
   - Seleciona **estado** com distribuição ponderada (SP: 25%, RJ: 10%, etc)
   - Calcula **renda** baseada no perfil (multiplicador: 0.5x a 3x)
   - Define **risco inicial** (inversamente proporcional à idade da conta)
   - Gera **2-3 dispositivos** por cliente
2. Retorna `CustomerIndex` (leve: ~80 bytes) para workers

**Gargalos Identificados:**

| # | Gargalo | Severidade | Impacto | Causa |
|---|---------|-----------|--------|-------|
| 1 | **Serialização de Faker** | 🟠 MÉDIA | +300ms por worker | Cada worker cria `Faker('pt_BR')` do zero; não é reutilizável entre workers |
| 2 | **Validação de CPF sequencial** | 🟡 BAIXA | +50ms/1000 CPFs | Algorithm pesado (Luhn duplo) mas only validada ao final |
| 3 | **Distribuição ponderada com random.choices** | 🟡 BAIXA | Negligenciável | Chamado por cliente (melhorar com cache) |
| 4 | **Sem cache de profiles** | 🟡 BAIXA | +10% chamadas desnecessárias | Lookups repetidos de `get_profile()` |

**Recomendação:** Use `numba.jit` para CPF ou cache Faker entre workers.

---

### 2️⃣ **GERAÇÃO DE TRANSAÇÕES** (`worker_generate_batch()`)

**Entrada:** 1000 transações por arquivo, ~100 arquivos

**Processo (por transação):**
1. **Determina fraude:** `random.random() < fraud_rate` (naive)
2. **Seleciona tipo:** PIX (42%), CREDIT_CARD (22%), etc (weighted)
3. **Seleciona MCC:** 300+ MCCs com pesos (profile-aware se `use_profiles=True`)
4. **Calcula valor:** Distribuição exponencial + ajuste por fraude/profile
5. **Seleciona merchant:** ~100k mercadores por MCC (random.choice)
6. **Gera geolocalização:** Lat/Lon Brasil (random + contaminação por fraude)
7. **Seleciona canal:** MOBILE_APP (60%), WEB (25%), etc
8. **Adiciona campos específicos:**
   - PIX: key_type, destination_bank
   - CARD: número hash, bandeira, 3DS, CVV
   - BOLETO: código, vencimento
9. **Calcula risk indicators:** 
   - distância última transação
   - tempo desde última transação
   - velocidade (txns/24h)
10. **Escreve em JSONL direto** (streaming - sem acumular em memória)

**Streaming vs Batch:**
- **JSONL:** Escreve linha por linha (memory-efficient)
- **CSV/Parquet:** Acumula lista em memória → flush ao exporter

**Gargalos Identificados:**

| # | Gargalo | Severidade | Impacto | Causa |
|---|---------|-----------|--------|-------|
| 1 | **random.choices() chamado por transação** | 🔴 ALTA | ~30% do tempo | Sem cache de weights; rebuild lista a cada vez |
| 2 | **get_merchants_for_mcc()** | 🟠 MÉDIA | ~15% do tempo | Lookup sequencial em lista; sem cache; ~2-5 merchants/MCC |
| 3 | **Cálculo de valor (exponencial)** | 🟠 MÉDIA | ~10% do tempo | 3-4 random.random() + operações math por transação |
| 4 | **Serialização JSON (dumps)** | 🟡 BAIXA | ~5% (tolerável) | Necessário mas otimizável com separators já usado |
| 5 | **Generate IP Brasil** | 🟡 BAIXA | ~2% | Concatenação string + random; melhor com format() |
| 6 | **Sem reutilização de pares customer-device** | 🟡 BAIXA | +5-10% random overhead | Usa `random.choice(pairs)` 1000x sem índice |
| 7 | **Campos de risco calculados inutilmente** | 🟠 MÉDIA | ~8% | time_since_last_txn sempre None; distance sempre None |

**Fórmula de Valor (problema):**
```python
# Atual: Sem contexto histórico real
valor_base = lognorm(mu=4.8, sigma=1.2)  # ~EUR 122
if is_fraud:
    valor_base *= random.uniform(1.5, 3)  # fraude = mais caro arbitrariamente
if mcc_info['risk'] == 'HIGH':
    valor_base *= 1.2
```

**Problema:** Não correlaciona com histórico do cliente (income, velocity).

---

### 3️⃣ **EXPORTADORES**

#### **JSONL (JSON Lines)**
- ✅ **Streaming direto** → sem acumular em memória
- ✅ Compatível com ferramentas big data (Spark, DuckDB, BigQuery)
- ✅ Ideal para datasets >1GB
- ⚠️ Sem índices → slower para busca
- 📊 ~500 bytes/transação → 1GB = ~2M transações

#### **CSV**
- ⚠️ **Acumula em memória** antes de escrever
- ⚠️ Flatten de objetos nested → colunas extras
- ✅ Compatível com Excel, Pandas
- ⚠️ Lento para >100MB

#### **Parquet**
- ⚠️ **Acumula em memória** (requer DataFrame)
- ✅ Compressão (zstd: 10-30x melhor que JSON)
- ✅ Colunar → queries eficientes
- ✅ MinIO otimizado (ProcessPool para bypass GIL)
- 📊 ~50-100 bytes/transação comprimido

#### **MinIO/S3**
- ✅ Upload paralelo (ThreadPool + ProcessPool)
- ⚠️ Sem retry/timeout configurável
- ⚠️ Sem validação ETag
- ⚠️ Credentials em memória (ProcessPool cria nova conexão/worker)

**Gargalos:**

| # | Gargalo | Severidade | Impacto | Formato |
|---|---------|-----------|--------|---------|
| 1 | **CSV: acumula lista inteira** | 🔴 ALTA | OOM em >1GB | CSV |
| 2 | **Parquet: DataFrame inteira** | 🔴 ALTA | OOM em >1GB | Parquet |
| 3 | **MinIO: sem retry em 503** | 🟠 MÉDIA | Falha silenciosa | S3/MinIO |
| 4 | **Flatten recursivo em CSV** | 🟡 BAIXA | +3-5% overhead | CSV |

---

### 4️⃣ **PARALELISMO**

#### **Arquitetura Atual:**

```
FASE 1 (SEQUENCIAL):
  - generate_customers_and_devices() → 1 process
  - Tempo: ~2s para 10k clientes

FASE 2 (PARALELO - ProcessPool + ThreadPool):
  - ProcessPool: Parquet (CPU-bound, bypass GIL)
  - ThreadPool: JSONL, CSV (I/O-bound)
  - Chunk size: 128MB/arquivo → ~256k transações
  - Workers: 8 (default = CPU count)
  
FASE 3 (SEQUENCIAL):
  - generate_drivers() → 1 process
  - Tempo: ~1s para 1000 drivers

FASE 4 (PARALELO):
  - Idem Fase 2 para rides
```

**Gargalos:**

| # | Gargalo | Severidade | Impacto | Solução |
|---|---------|-----------|--------|---------|
| 1 | **Fase 1 + 3 sequenciais** | 🟠 MÉDIA | +5-10% tempo total | Paralelizar geradores com ThreadPool |
| 2 | **GIL com ThreadPool em Faker** | 🔴 ALTA | Overhead sincronização | Use ProcessPool para customer gen |
| 3 | **Sem rebalanceamento de workers** | 🟡 BAIXA | Straggler problem | Usar dynamic task scheduling |
| 4 | **Pool.imap_unordered é rápido mas não mostra progresso dinâmico** | 🟡 BAIXA | UX (spinner fica preso) | Usar Executor com as_completed() |

---

## 📊 Perfis Comportamentais

**Atributo:** Customiza geração de transações baseado no perfil do cliente

```python
PROFILES = {
    'young_digital': {      # 18-35, renda 1500-3000 BRL
        'transactions': {
            'PIX': 50,      # Prefere PIX
            'MOBILE_TOPUP': 30,
            'CREDIT_CARD': 20,
        },
        'merchants': ['Netflix', 'Spotify', 'Uber', ...],
        'channels': {'MOBILE_APP': 90, 'WEB': 10},
        'value_range': (10, 200),
    },
    'business_owner': {     # 40-65, renda 8000-50k BRL
        'transactions': {
            'TED': 40,      # Transferências para fornecedores
            'BOLETO': 30,
            'CREDIT_CARD': 30,
        },
        'merchants': ['Amazon', 'SAP', 'Loggi', ...],
        'value_range': (500, 10000),
    },
    # ... 5 outros perfis
}
```

**Problema:** Perfis são **estáticos** → sem evolução no tempo (cliente não muda hábitos).

---

## 🎭 Estratégia de Fraude

### **Abordagem Implementada (Pipeline de Enrichers):**

```python
# 1. Decide se é fraude (Bernoulli com fraud_rate)
is_fraud = random.random() < fraud_rate
fraud_type = weighted_choice(FRAUD_TYPES_LIST, FRAUD_TYPES_WEIGHTS)

# 2. Gera TX base
tx = {base_fields}

# 3. Monta GeneratorBag com contexto
bag = GeneratorBag(is_fraud=is_fraud, fraud_type=fraud_type, ...)

# 4. Pipeline de 8 enrichers em sequência (ORDEM CRÍTICA)
for enricher in [TemporalEnricher, GeoEnricher, FraudEnricher, PIXEnricher,
                 DeviceEnricher, SessionEnricher, RiskEnricher, BiometricEnricher]:
    enricher.enrich(tx, bag)  # Muta tx in-place

# 5. fraud_risk_score calculado pelo RiskEnricher (17 sinais, 0-100)
```

**FraudEnricher** aplica características do padrão (25 tipos em `config/fraud_patterns.py`):
- `CONTA_TOMADA`: amount_multiplier (1.5–5x), time_anomaly HIGH, device_anomaly HIGH
- `PIX_GOLPE`: new_beneficiary_prob 0.95, channel_preference PIX
- `ENGENHARIA_SOCIAL`: valor aparentemente normal, sem anomalia de device
- [+22 outros padrões com características distintas]

**RiskEnricher** computa `fraud_risk_score` via 17 sinais independentes:
```python
# Os 5 sinais de maior peso:
_W_ACTIVE_CALL  = 35  # Vítima no telefone com fraudador
_W_EMULATOR     = 35  # Device emulado (MALWARE_ATS)
_W_ROOTED       = 30  # Device rooted/jailbroken
_W_TYPING_BOT   = 30  # Typing < 15ms → script
_W_ACCEL_SESSION = 28 # Zero accel + sessão < 5s → device estático
```

---

## 🔧 Estado das Otimizações (v4.17)

As otimizações abaixo foram **implementadas** nas versões v4.x:

| Otimização | Status | Onde |
|------------|--------|------|
| Cache de Weights | ✅ Implementado | `utils/weight_cache.py` — WeightCache (bisect O(log n)) |
| Cache de Merchants | ✅ Implementado | `config/merchants.py` — dict cache por MCC |
| PrecomputeBuffers (IPs, hashes, floats) | ✅ Implementado | `utils/precompute.py` — ring buffer 10k valores |
| CustomerSession (velocity, merchant novelty) | ✅ Implementado | `utils/streaming.py` — CustomerSessionState |
| Fraude contextualizada por padrão | ✅ Implementado | Pipeline de enrichers + `config/fraud_patterns.py` |
| fraud_risk_score (17 sinais) | ✅ Implementado | `generators/score.py` |
| GIL bypass para streaming | ✅ Implementado | `utils/parallel.py` — ParallelStreamManager |

**Ainda pendente (P3):** CSV/Parquet streaming OOM para datasets >1GB — acumula list em memória antes de escrever.

---

## 📈 Benchmarks e Capacidades

### **Performance (v4.17, com WeightCache + PrecomputeBuffers)**
```
Hardware: 18-core Linux, Python 3.12

Transactions  8 workers:  ~58.000 evt/s  (~125 MB/s JSONL)
Rides         4 workers:  ~67.000 evt/s  (~77 MB/s JSONL)
All types     4 workers:  ~55.000 evt/s  (~119 MB/s JSONL)

1 GB JSONL: ~8-10s com 8 workers
```

Ver `benchmarks/comprehensive_benchmark.py` para regenerar e `docs/performance/CAPACITY_PLANNING.md` para projeções de VPS.

### **Escalabilidade:**
| Tamanho | Customers | Transactions | Tempo (~8w) |
|---------|-----------|--------------|-------------|
| 1GB     | 10k       | 2.5M         | ~10s        |
| 10GB    | 100k      | 25M          | ~90s        |
| 100GB   | 1M        | 250M         | ~15min      |
| 1TB     | 10M       | 2.5B         | ~150min     |

---

## 🚨 Problemas Críticos

### **🔴 SEVERIDADE CRÍTICA**

1. **Sem Validação de Integridade Referencial**
   - Devices referencia customer_id inexistente ✓ (dentro de bounds)
   - Mas sem verificar se ID está realmente no conjunto
   - Impacto: 0-1% taxa de erro, invisível para small datasets

2. **Sem Retry em Falhas MinIO**
   - Se MinIO cair, perdem-se uploads parciais
   - Sem checksum ETag validation
   - Impacto: Data loss em produção

3. **Sem Validação de Limites (Limits)**
   - Card limit, account limit, daily limit
   - Todas transações são approved (exceto decode)
   - Impacto: Dados não realistas para teste de limite

### **🟠 SEVERIDADE ALTA**

4. **GIL + ThreadPool em Faker**
   - CustomerGenerator usa Faker (Python)
   - ThreadPool com múltiplos threads causa serialização
   - Impacto: Potencial deadlock em >16 workers

5. **Sem Suporte a Seed Global**
   - Seed local por worker
   - Não há garantia de reprodutibilidade com diferentes worker counts
   - Impacto: Testes não determinísticos

6. **Sem Tratamento de Exceção em Worker**
   - Se um worker falha, não há retry
   - Batch inteiro é perdido
   - Impacto: +1GB de dados faltando silenciosamente

---

## 💡 Quick Wins (Implementar Primeiro)

| # | Mudança | Complexidade | Impacto | Tempo |
|----|---------|-------------|--------|--------|
| 1  | Cache de transaction type weights | ⭐ Trivial | 25% speedup | 10min |
| 2  | Remover campos de risco None | ⭐ Trivial | 5% speedup | 5min |
| 3  | Add retry em MinIO (3 tentativas) | ⭐⭐ Simples | Reliability ++| 30min |
| 4  | Paralelizar phase 1 com ThreadPool | ⭐⭐ Simples | 15% total | 1h |
| 5  | Logging de erros em workers | ⭐⭐ Simples | Debuggability | 30min |
| 6  | CSV streaming (batch 10k rows) | ⭐⭐⭐ Médio | OOM fix | 2h |
| 7  | Fraud contextualization por tipo | ⭐⭐⭐ Médio | Realismos | 4h |
| 8  | Customer session state tracking | ⭐⭐⭐⭐ Complexo | Realistic patterns | 1 dia |

---

## 🎯 Conclusão

**Pontos Fortes:**
- ✅ Streaming memory-efficient (JSONL)
- ✅ Paralelismo bem implementado (ProcessPool vs ThreadPool)
- ✅ Dados brasileiros realistas (CPF, banks, MCCs)
- ✅ Múltiplos formatos (JSONL, CSV, Parquet)
- ✅ Suporte MinIO/S3 robusto

**Pontos Fracos:**
- ❌ Fraude muito simplista (sem padrões)
- ❌ Performance (20-30% perda em random.choices)
- ❌ CSV/Parquet sem streaming (OOM >1GB)
- ❌ Sem histórico de cliente (comportamento estático)
- ❌ Sem retry/error handling em produção

**Recomendação:** Implementar **Quick Wins** primeiro (2h) depois atacar **Fraude Contextualizada** (4-8h) para máximo impacto em realismo.

