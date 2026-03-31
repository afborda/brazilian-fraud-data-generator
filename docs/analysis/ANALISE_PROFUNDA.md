# Análise Profunda - synthfin-data v4.15.1

## 📋 Sumário Executivo

O projeto é um **gerador de dados sintéticos de fraude brasileira** otimizado para produção. Cria transações financeiras realistas (PIX, cartão de crédito, etc.) e dados de corridas (Uber, 99, etc.) com padrões comportamentais, possibilidade de fraude configurável e múltiplos formatos de exportação (JSONL, CSV, Parquet).

**Stack:**
- Python 3
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
│   ├── transaction.py   # Transações (PIX, cartão, etc)
│   └── ride.py          # Corridas de ride-share
├── models/              # Dataclasses dos entidades
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

### **Abordagem Atual (Simplista):**
```python
is_fraud = random.random() < fraud_rate  # Bernoulli simples
if is_fraud:
    fraud_type = weighted_choice(FRAUD_TYPES)  # Ex: account_takeover
    valor *= 1.5  # Multiplicador arbitrário
    # Alguns campos marcam como suspeito (unusual_time, new_beneficiary)
```

### **Problemas:**
1. **Não correlaciona com histórico** → fraude em dia anormal não detecta
2. **Sem sequências de fraude** → real: fraude vem em clusters
3. **Campos de risco isolados** → não há pattern matching
4. **Fraud types não determinam características** → "account_takeover" não muda IP/device/location
5. **Sem contextualização temporal** → mesma taxa 24/7 (real: picos à noite)

### **Exemplos de Padrões Perdidos:**
- ✅ Account takeover: `new_device + different_location + high_velocity`
- ✅ Card cloning: `same_merchant_series + different_IP`
- ✅ Social engineering: `round_numbers + unusual_time + new_beneficiary`
- ✅ Money laundering: `high_volume + round_values + same_beneficiary`

---

## 🔧 Melhorias Recomendadas

### **CURTO PRAZO (1-2 dias)**

#### **1. Cache de Weights (30% speedup transações)**
```python
# ANTES: random.choices() rebuild weights cada vez
tx_type = random.choices(TX_TYPES_LIST, weights=TX_TYPES_WEIGHTS)[0]

# DEPOIS: pre-compute cumulative distribution
cumsum = np.cumsum(TX_TYPES_WEIGHTS)  # Uma vez!
idx = np.searchsorted(cumsum, random.random() * cumsum[-1])
tx_type = TX_TYPES_LIST[idx]
```

#### **2. Cache de Merchants (20% speedup)**
```python
# ANTES:
merchants = get_merchants_for_mcc(mcc_code)  # DB lookup toda vez
merchant_name = random.choice(merchants)

# DEPOIS:
MERCHANTS_CACHE = {}  # Build once
merchant_name = random.choice(MERCHANTS_CACHE[mcc_code])
```

#### **3. Remover campos de risco desnecessários (5% speedup)**
```python
# ANTES: Calcula fields que sempre são None
distance_from_last_txn_km = None  # Sem histórico
time_since_last_txn_min = None

# DEPOIS: Remover ou substituir por algo realista
# Se quer histórico: manter estado (não é sintético puro)
# Se quer sintético puro: remover completamente
```

#### **4. Melhorar IP Brasil geração (2% speedup)**
```python
# ANTES: Concatenação string + random 4x
ip = f"{prefix}.{r()}.{r()}.{r()}"

# DEPOIS: Tuple de inteiros (mais rápido)
ip = f"{prefix}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
```

---

### **MÉDIO PRAZO (1 semana)**

#### **5. Fraude Contextualizada (Realismos +40%)**
```python
def generate_fraud(customer_profile, last_transactions):
    """Gera fraude com padrões realistas."""
    
    if fraud_type == 'account_takeover':
        # Device DIFERENTE do histórico
        device_id = generate_new_device()
        
        # IP DIFERENTE da localização do cliente
        customer_state = customer['state']
        location_state = random.choice([s for s in STATES if s != customer_state])
        lat, lon = get_state_center(location_state)
        
        # Valor anormalmente ALTO vs histórico
        avg_valor = np.mean([t['amount'] for t in last_transactions[-30:]])
        valor = avg_valor * random.uniform(5, 10)
        
        # Hora anormal
        unusual_time = random.choice(hours=[22, 23, 0, 1, 2, 3])
        
    elif fraud_type == 'card_cloning':
        # Mesmo merchant repetido
        merchant = last_merchants[-1]  # Clone da última
        
        # Valores similares (padrão: teste com valores baixos depois altos)
        valor = [random.uniform(1, 5) for _ in range(3)] + [5000]
```

#### **6. Série Temporal de Comportamento**
```python
# ANTES: Cada transação independente
# DEPOIS: Manter estado do cliente no dia
class CustomerSession:
    def __init__(self):
        self.transactions_today = []
        self.merchants_visited = set()
        self.velocity = 0
        self.accumulated_amount = 0.0
    
    def add_transaction(self, tx):
        self.transactions_today.append(tx)
        self.velocity = len(self.transactions_today)
        self.accumulated_amount += tx['amount']
        # Usa para calcular limits, risk, etc
```

#### **7. Paralelizar Customer Generation (20% speedup Fase 1)**
```python
# ANTES: Sequential loop 10k vezes
for i in range(num_customers):
    customer_gen.generate(f"CUST_{i}")

# DEPOIS: ProcessPool com chunk
def _generate_customer(customer_id):
    return customer_gen.generate(customer_id)

with ProcessPool(max_workers=8) as pool:
    customers = pool.map(_generate_customer, [f"CUST_{i}" for i in range(num_customers)])
```

#### **8. CSV/Parquet Streaming (OOM fix)**
```python
# ANTES: Parquet acumula DataFrame inteira
transactions = [...]  # 1M registros
df = pd.DataFrame(transactions)
df.to_parquet(path)  # OOM se >10GB

# DEPOIS: Streaming Parquet writer
writer = ParquetWriter(path)
for batch in batches_of_1000:
    df = pd.DataFrame(batch)
    writer.write_table(pa.Table.from_pandas(df))
writer.close()
```

---

### **LONGO PRAZO (2+ semanas)**

#### **9. Persistência de Estado para Customers (Realismo +50%)**
```python
# Criar arquivo CSV para cada cliente com histórico
# | date | merchant | amount | location | device | ...
# Simula velocidade, padrões, anomalias reais

class CustomerHistoryTracker:
    def load(self, customer_id):
        """Carrega histórico dos últimos 30 dias."""
        df = pd.read_csv(f"history/{customer_id}.csv")
        return df
    
    def calculate_baseline(self, transactions):
        """Mean, std, percentiles."""
        return {
            'avg_amount': np.mean(transactions['amount']),
            'avg_velocity': len(transactions) / 30,  # por dia
            'favorite_merchants': Counter(transactions['merchant']),
            'preferred_times': Counter(transactions['hour']),
        }
```

#### **10. Geração de Anomalias Realistas**
```python
# Em vez de fraude aleatória, gerar patterns:
# 1. Velocity (N transações em K minutos)
# 2. Impossible travel (2 cidades, distância impossível em tempo)
# 3. Round amounts (2000, 5000, 10000 BRL exatos)
# 4. Value burst (5x média historicamente)
# 5. New beneficiary (primeira vez transferência para CPF)
# 6. Unusual merchant category (cliente varejo compra em B2B)

def detect_anomalies(transaction, history):
    """Marca campos de risco baseado em história."""
    anomalies = []
    
    baseline = calculate_baseline(history)
    
    if transaction['amount'] > baseline['avg_amount'] * 5:
        anomalies.append('high_value')
        transaction['anomaly_score'] += 0.3
    
    # ... mais 10+ heurísticas
    
    return transaction
```

#### **11. Integração com Machine Learning**
```python
# Treinar modelo de detecção de fraude nas primeiras rodadas
# Usar para calibrar fraud_rate dinamicamente

from sklearn.ensemble import IsolationForest

# Coletar transações sintéticas de dias anteriores
X = fetch_generated_transactions(days=7)

model = IsolationForest(contamination=0.02)
model.fit(X)

# Usar para score de fraude
fraud_score = -model.decision_function(new_transaction)  # 0-1
is_fraud = fraud_score > threshold
```

#### **12. Dados de Rejeição Realistas**
```python
# ANTES: is_fraud → status = 'APPROVED' | 'DECLINED' (50/50)
# DEPOIS: Context-based rejection

refusal_probabilities = {
    'INSUFFICIENT_BALANCE': 0.3,
    'FRAUD_SUSPECT': 0.2,
    'LIMIT_EXCEEDED': 0.2,
    'CVV_ERROR': 0.15,
    'CARD_BLOCKED': 0.1,
    'CARD_EXPIRED': 0.05,
}

# Se valor alto + new_beneficiary → 50% FRAUD_SUSPECT
# Se autofraude → 80% APPROVED (sistema confia no cliente)
# Se account_takeover → 100% BLOCKED
```

---

## 📈 Benchmarks e Capacidades

### **Performance Atual (v4-beta)**
```
Hardware: CPU 8-core, 16GB RAM
Target: 1GB JSONL

Phase 1 (Customers):   2.1s  (10k clientes, 30k devices)
Phase 2 (Transactions): 18.3s (2.5M transações, 10 workers)
Phase 3 (Drivers):     0.8s  (1000 drivers)
Phase 4 (Rides):       15.2s (1.6M rides, 10 workers)
─────────────────────────────
Total:                 36.4s (~27.3MB/s throughput)

Output size: 1.02GB JSONL
```

### **Análise de Bottleneck:**
- Phase 2 + 4 (paralelizadas): 33.5s de 36.4s = **92% do tempo**
- Se cache weights (25% speedup): ~25s
- Se streaming CSV (OOM fix): ~+10s vs atual (Parquet + cache)

### **Escalabilidade Projetada:**
| Tamanho | Customers | Transactions | Tempo Estimado | Files |
|---------|-----------|--------------|----------------|-------|
| 1GB     | 10k       | 2.5M         | 36s            | 10    |
| 10GB    | 100k      | 25M          | 360s (6m)      | 100   |
| 100GB   | 1M        | 250M         | 3600s (60m)    | 1000  |
| 1TB     | 10M       | 2.5B         | 10h            | 10k   |

**Problema a escala:** Fase 1 (customer gen) não paralelizável trivialmente → seria gargalo em 1TB+.

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

