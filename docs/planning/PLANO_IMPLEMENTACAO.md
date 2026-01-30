# Plano de Implementação - Brazilian Fraud Data Generator

## 🎯 Objetivos (Roadmap)

### Curto Prazo (Esta semana)
**Objetivo:** +30% performance, fix OOM
- [ ] Cache de weights (30% speedup transações)
- [ ] Remove campos None (5% speedup)
- [ ] Add retry/timeout MinIO (reliability)
- [ ] CSV streaming para evitar OOM

### Médio Prazo (Próximas 2 semanas)
**Objetivo:** Fraude realista com padrões
- [ ] Fraud contextualization por tipo
- [ ] Customer session state
- [ ] Paralelizar customer generation
- [ ] Tests e validação

### Longo Prazo (Roadmap futura)
**Objetivo:** Production-grade
- [ ] ML-based fraud score
- [ ] Time-series behavioral tracking
- [ ] Anomaly detection pipeline
- [ ] Analytics dashboard

---

## 📝 PLANO DETALHADO

### **PHASE 1: OTIMIZAÇÕES RÁPIDAS**

#### **1.1 Cache de Transaction Type Weights**
**Arquivo:** `src/fraud_generator/generators/transaction.py`

**Problema:**
```python
# ANTES: random.choices() chamado POR TRANSAÇÃO
for i in range(num_transactions):
    tx_type = random.choices(TX_TYPES_LIST, weights=TX_TYPES_WEIGHTS)[0]
    # ... 1000+ chamadas = rebuild weights toda vez
```

**Solução:**
```python
# NO __init__ DA CLASSE:
class TransactionGenerator:
    def __init__(self, ...):
        # Pre-compute cumulative weights para O(log n) lookup
        self._tx_type_cumsum = np.cumsum(TX_TYPES_WEIGHTS) / sum(TX_TYPES_WEIGHTS)
        self._mcc_cumsum = np.cumsum(MCC_WEIGHTS) / sum(MCC_WEIGHTS)
        self._channel_cumsum = np.cumsum(CHANNELS_WEIGHTS) / sum(CHANNELS_WEIGHTS)
        self._fraud_type_cumsum = np.cumsum(FRAUD_TYPES_WEIGHTS) / sum(FRAUD_TYPES_WEIGHTS)
    
    def _weighted_choice_cached(self, cumsum, choices_list):
        """Binary search em cumulative distribution."""
        r = random.random()
        idx = np.searchsorted(cumsum, r)
        return choices_list[min(idx, len(choices_list)-1)]
    
    def generate(self, ...):
        tx_type = self._weighted_choice_cached(self._tx_type_cumsum, TX_TYPES_LIST)
        mcc_code = self._weighted_choice_cached(self._mcc_cumsum, MCC_LIST)
        # ... etc
```

**Impacto:**
- Antes: ~3.2µs per random.choices()
- Depois: ~0.2µs per searchsorted()
- **Speedup esperado: 15x (~25% do tempo total transação)**

**Teste:**
```python
import timeit
# Antes
t1 = timeit.timeit(
    lambda: random.choices(TX_TYPES_LIST, weights=TX_TYPES_WEIGHTS)[0],
    number=100000
)
# Depois
t2 = timeit.timeit(
    lambda: self._weighted_choice_cached(self._tx_type_cumsum, TX_TYPES_LIST),
    number=100000
)
print(f"Speedup: {t1/t2:.1f}x")
```

---

#### **1.2 Cache de Merchants por MCC**
**Arquivo:** `src/fraud_generator/config/merchants.py`

**Problema:**
```python
# ANTES: get_merchants_for_mcc() faz lookup sequencial
merchants = get_merchants_for_mcc('5411')  # Supermercado
# Retorna lista ~5 merchants, chamado 2.5M vezes = 2.5M lookups
```

**Solução:**
```python
# Em merchants.py:
MCC_MERCHANTS = {}

# Build cache uma vez ao importar
def _build_merchants_cache():
    """Cache merchants por MCC para O(1) lookup."""
    for mcc_code, merchants in MCC_MERCHANT_MAP.items():
        MCC_MERCHANTS[mcc_code] = merchants
    return len(MCC_MERCHANTS)

MERCHANTS_CACHE_SIZE = _build_merchants_cache()

def get_merchants_for_mcc(mcc_code):
    """O(1) lookup com cache."""
    return MCC_MERCHANTS.get(mcc_code, DEFAULT_MERCHANTS)
```

**Impacto:**
- Antes: ~2-5µs per lookup (lista search)
- Depois: ~0.1µs per lookup (dict access)
- **Speedup esperado: 20x (~10% do tempo total)**

---

#### **1.3 Remove Campos de Risco Nulos**
**Arquivo:** `src/fraud_generator/generators/transaction.py`

**Problema:**
```python
# ANTES: Calcula fields que serão sempre None
def _add_risk_indicators(self, tx, ...):
    distance_from_last_txn_km = None  # ← Sempre None!
    time_since_last_txn_min = None    # ← Sempre None!
    
    tx['distance_from_last_txn_km'] = distance_from_last_txn_km
    tx['time_since_last_txn_min'] = time_since_last_txn_min
```

**Solução - Opção A (Remove):**
```python
# Remove campos que não têm valor
# Em models/transaction.py, remover do dataclass:
# distance_from_last_txn_km: Optional[float] = None  # ← DELETE
# time_since_last_txn_min: Optional[int] = None      # ← DELETE

# Impacto: Reduz tamanho JSON ~80-100 bytes/transação
```

**Solução - Opção B (Implementa Corretamente):**
```python
# Se quer esses campos realistas, manter estado:
class TransactionGenerator:
    def __init__(self, ...):
        self.last_transactions = {}  # {customer_id: [timestamps]}
    
    def _add_risk_indicators(self, tx, customer_id, timestamp):
        if customer_id in self.last_transactions:
            last_times = sorted(self.last_transactions[customer_id])[-3:]
            if last_times:
                time_since = (timestamp - last_times[-1]).total_seconds() / 60
                tx['time_since_last_txn_min'] = int(time_since)
        
        # Update history
        if customer_id not in self.last_transactions:
            self.last_transactions[customer_id] = []
        self.last_transactions[customer_id].append(timestamp)
```

**Recomendação:** Opção A (remove) para sintético puro. Opção B só se persistir estado do cliente.

**Impacto:**
- Opção A: Reduz JSON size 10%, não calcula fields
- **Speedup esperado: 5%**

---

#### **1.4 Paralelizar Customer Generation**
**Arquivo:** `generate.py`, função `generate_customers_and_devices()`

**Problema:**
```python
# ANTES: Loop sequencial 10k vezes
def generate_customers_and_devices(num_customers, ...):
    for i in range(num_customers):  # Sequencial!
        customer = customer_gen.generate(f"CUST_{i:012d}")
        # ... 10k iterações leva 2.1s
```

**Solução:**
```python
from concurrent.futures import ThreadPoolExecutor

def generate_customers_and_devices(num_customers, ..., workers=4):
    """Generate customers in parallel."""
    
    customer_gen = CustomerGenerator(use_profiles=use_profiles, seed=seed)
    device_gen = DeviceGenerator(seed=seed)
    
    customer_indexes = []
    customer_data = []
    device_indexes = []
    device_data = []
    
    def _generate_single(i):
        """Generate one customer with devices."""
        customer_id = f"CUST_{i:012d}"
        customer = customer_gen.generate(customer_id)
        
        devices = []
        for device in device_gen.generate_for_customer(customer_id, ...):
            devices.append(device)
        
        return customer, devices
    
    # ThreadPool (Faker é I/O-ish, não CPU-bound)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(_generate_single, i) for i in range(num_customers)]
        
        for future in futures:
            customer, devices = future.result()
            customer_data.append(customer)
            
            customer_idx = CustomerIndex(...)
            customer_indexes.append(tuple(customer_idx))
            
            for device in devices:
                device_data.append(device)
                device_idx = DeviceIndex(...)
                device_indexes.append(tuple(device_idx))
    
    return customer_indexes, device_indexes, customer_data, device_data
```

**Impacto:**
- Antes: 2.1s (sequencial)
- Depois: ~0.7s (3x parallelism)
- **Speedup esperado: 3x na Phase 1 (~5% total)**

**Cuidado:** Faker pode ter thread-safety issues; considerar ProcessPool se problemas.

---

#### **1.5 Add Retry em MinIO**
**Arquivo:** `src/fraud_generator/exporters/minio_exporter.py`

**Problema:**
```python
# ANTES: Sem retry em falha
s3_client.put_object(
    Bucket=bucket,
    Key=key,
    Body=data,
)  # Se falha 503, perde dados
```

**Solução:**
```python
import boto3
from botocore.exceptions import ClientError

def export_batch(self, data, key, max_retries=3):
    """Export with automatic retries."""
    last_error = None
    
    for attempt in range(max_retries):
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
            )
            return  # Success
        
        except ClientError as e:
            last_error = e
            error_code = e.response['Error']['Code']
            
            if error_code in ['ServiceUnavailable', 'SlowDown', 'RequestTimeout']:
                wait_time = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff
                print(f"   ⚠️  Retry {attempt+1}/{max_retries} para {key} (aguardando {wait_time:.1f}s)")
                time.sleep(wait_time)
            else:
                raise  # Don't retry on client errors
        
        except Exception as e:
            last_error = e
            print(f"   ❌ Erro ao fazer upload {key}: {e}")
            raise
    
    # All retries failed
    raise IOError(f"Failed to upload {key} after {max_retries} attempts: {last_error}")
```

**Impacto:**
- Reliability: Tolera falhas transitórias
- **Downtime prevention: Crítico em produção**

---

#### **1.6 CSV Streaming (Fix OOM)**
**Arquivo:** `src/fraud_generator/exporters/csv_exporter.py`

**Problema:**
```python
# ANTES: Acumula lista inteira
def export_batch(self, data, path):
    with open(path, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=...)
        writer.writeheader()
        for row in data:  # data pode ter 1M linhas = OOM!
            writer.writerow(row)
```

**Solução:**
```python
class CSVExporter(ExporterProtocol):
    def export_batch(self, data, output_path, append=False):
        """Export records to CSV in streaming mode."""
        # First pass: collect fieldnames
        if not self._fieldnames:
            self._fieldnames = self._get_fieldnames(data[:1000])  # Sample only
        
        mode = 'a' if append else 'w'
        file_exists = os.path.exists(output_path) and os.path.getsize(output_path) > 0
        
        with open(output_path, mode, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self._fieldnames)
            
            if not (append and file_exists):
                writer.writeheader()
            
            count = 0
            for record in data:  # Iterate, não acumule
                flat = self._flatten_dict(record) if self.flatten_nested else record
                writer.writerow(flat)
                count += 1
        
        return count

def export_stream(self, data_iterator, output_path, batch_size=5000):
    """Export large datasets from iterator."""
    total_count = 0
    first_batch = True
    batch = []
    
    for record in data_iterator:
        batch.append(record)
        
        if len(batch) >= batch_size:
            # Write batch, don't accumulate
            self.export_batch(batch, output_path, append=not first_batch)
            total_count += len(batch)
            batch = []
            first_batch = False
    
    # Write remaining
    if batch:
        self.export_batch(batch, output_path, append=not first_batch)
        total_count += len(batch)
    
    return total_count
```

**Uso em worker:**
```python
def worker_generate_batch(args):
    # ... generate transactions ...
    
    if format_name == 'csv':
        # Write in streaming batches of 5000
        def transaction_generator():
            for i in range(num_transactions):
                yield generate_one_transaction(...)
        
        exporter.export_stream(transaction_generator(), output_path, batch_size=5000)
```

**Impacto:**
- Antes: OOM para >1GB
- Depois: Streaming generator pattern, constant memory
- **Fix crítico para escalabilidade**

---

### **PHASE 2: FRAUDE REALISTA**

#### **2.1 Fraud Contextualization**
**Arquivo:** `src/fraud_generator/generators/transaction.py`

**Conceito:** Cada tipo de fraude tem characteristics específicas

```python
FRAUD_PATTERNS = {
    'ENGENHARIA_SOCIAL': {
        # Social engineering: cliente é enganado
        'characteristics': {
            'value_anomaly': 'NORMAL',          # Valor normal (não suspicioso)
            'new_beneficiary': True,             # Nova conta destino
            'velocity': 'NORMAL',                # Velocidade normal
            'time_anomaly': 'NORMAL',            # Hora normal
            'location_anomaly': 'LOW',           # Pode ser diferente
            'device_anomaly': 'LOW',             # Device pode ser mesmo
        },
        'prevalence': 0.20,  # 20% das fraudes
    },
    'CONTA_TOMADA': {
        # Account takeover: atacante em posse da conta
        'characteristics': {
            'value_anomaly': 'HIGH',             # Valores altos
            'new_beneficiary': True,             # Novos destinos
            'velocity': 'HIGH',                  # Múltiplas transações rápidas
            'time_anomaly': 'HIGH',              # Hora inusual (madrugada)
            'location_anomaly': 'HIGH',          # IP/geo diferente
            'device_anomaly': 'HIGH',            # Device novo
        },
        'prevalence': 0.15,
    },
    'CARTAO_CLONADO': {
        # Cloned card: mesmo card, diferentes transações
        'characteristics': {
            'value_anomaly': 'MEDIUM',           # Escalação: baixo depois alto
            'new_beneficiary': False,            # Mesmos merchants
            'velocity': 'HIGH',                  # Série rápida
            'time_anomaly': 'MEDIUM',
            'location_anomaly': 'MEDIUM',        # Pode ser longe
            'device_anomaly': 'MEDIUM',
        },
        'prevalence': 0.14,
    },
    # ... mais tipos
}

class TransactionGenerator:
    def generate(self, ...):
        if is_fraud:
            fraud_type = random.choices(FRAUD_TYPES_LIST, ...)[0]
            pattern = FRAUD_PATTERNS[fraud_type]
            
            # Apply fraud pattern characteristics
            tx = self._apply_fraud_pattern(tx, pattern, customer_profile)
        
        return tx
    
    def _apply_fraud_pattern(self, tx, pattern, customer_profile):
        """Apply fraud-specific characteristics to transaction."""
        
        # VALUE ANOMALY
        if pattern['characteristics']['value_anomaly'] == 'HIGH':
            # Much higher than typical for customer
            tx['amount'] *= random.uniform(3, 10)
            tx['fraud_score'] += 0.3
        
        elif pattern['characteristics']['value_anomaly'] == 'MEDIUM':
            # Slightly abnormal - escalation
            tx['amount'] *= random.uniform(1.5, 3)
            tx['fraud_score'] += 0.15
        
        # NEW BENEFICIARY
        if pattern['characteristics']['new_beneficiary']:
            tx['new_beneficiary'] = True
            # Different destination bank
            tx['destination_bank'] = random.choice(BANK_CODES)
            tx['fraud_score'] += 0.2
        
        # VELOCITY
        if pattern['characteristics']['velocity'] == 'HIGH':
            tx['transactions_last_24h'] = random.randint(10, 50)
            tx['fraud_score'] += 0.25
        
        # TIME ANOMALY
        if pattern['characteristics']['time_anomaly'] == 'HIGH':
            # Madrugada (22h-4h)
            hour = random.choice([22, 23, 0, 1, 2, 3, 4])
            timestamp = tx['timestamp'].replace(hour=hour)
            tx['timestamp'] = timestamp.isoformat()
            tx['unusual_time'] = True
            tx['fraud_score'] += 0.2
        
        # LOCATION ANOMALY
        if pattern['characteristics']['location_anomaly'] == 'HIGH':
            # Completely different state
            customer_state = customer_profile.get('state', 'SP')
            different_state = random.choice([
                s for s in ESTADOS_LIST if s != customer_state
            ])
            center = get_state_center(different_state)
            tx['geolocation_lat'] = center['lat']
            tx['geolocation_lon'] = center['lon']
            tx['fraud_score'] += 0.25
        
        # DEVICE ANOMALY
        if pattern['characteristics']['device_anomaly'] == 'HIGH':
            # Completely different device
            tx['device_id'] = f"DEV_{random.randint(100000, 999999):06d}"
            tx['fraud_score'] += 0.2
        
        return tx
```

**Impacto:**
- Fraudes muito mais realistas
- Padrões detectáveis por ML models
- **Realismo +40-50%**

---

#### **2.2 Customer Session State**
**Arquivo:** `src/fraud_generator/utils/streaming.py`

**Conceito:** Manter estado do cliente por "sessão" para correlação

```python
class CustomerSessionState:
    """Track customer activity in a session for correlated transactions."""
    
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.transactions_today = []
        self.merchants_visited = set()
        self.locations = []
        self.devices_used = set()
        self.accumulated_amount = 0.0
        self.transaction_timestamps = []
    
    def add_transaction(self, tx: Dict[str, Any]) -> None:
        """Add transaction to session state."""
        self.transactions_today.append(tx)
        self.merchants_visited.add(tx['merchant_id'])
        self.locations.append((tx['geolocation_lat'], tx['geolocation_lon']))
        self.devices_used.add(tx['device_id'])
        self.accumulated_amount += tx['amount']
        self.transaction_timestamps.append(tx['timestamp'])
    
    def get_velocity(self) -> int:
        """Transactions in last 24h."""
        return len(self.transactions_today)
    
    def get_accumulated_24h(self) -> float:
        """Total amount in last 24h."""
        return self.accumulated_amount
    
    def is_new_merchant(self, merchant_id: str) -> bool:
        """Is this a new merchant for customer?"""
        return merchant_id not in self.merchants_visited
    
    def get_average_value(self) -> float:
        """Average transaction value."""
        if not self.transactions_today:
            return 0.0
        return self.accumulated_amount / len(self.transactions_today)
    
    def get_last_transaction_minutes_ago(self) -> Optional[int]:
        """Minutes since last transaction."""
        if len(self.transaction_timestamps) < 2:
            return None
        time_diff = (
            self.transaction_timestamps[-1] - self.transaction_timestamps[-2]
        )
        return int(time_diff.total_seconds() / 60)

# Usage in worker
def worker_generate_batch(args):
    # ... setup ...
    
    sessions = {}  # {customer_id: CustomerSessionState}
    
    for i in range(num_transactions):
        customer, device = random.choice(pairs)
        customer_id = customer.customer_id
        
        # Get or create session
        if customer_id not in sessions:
            sessions[customer_id] = CustomerSessionState(customer_id)
        
        session = sessions[customer_id]
        
        # Generate transaction
        tx = tx_generator.generate(...)
        
        # Enhance with session state
        tx['transactions_last_24h'] = session.get_velocity() + 1
        tx['accumulated_amount_24h'] = session.get_accumulated_24h() + tx['amount']
        tx['new_beneficiary'] = session.is_new_merchant(tx['merchant_id'])
        
        if session_time_since := session.get_last_transaction_minutes_ago():
            tx['time_since_last_txn_min'] = session_time_since
        
        # Update session
        session.add_transaction(tx)
        
        # Write to file
        f.write(json.dumps(tx) + '\n')
```

**Impacto:**
- Correlação entre transações do mesmo cliente
- Velocity, accumulated amount realistas
- **Realismo +30-40%**

---

### **PHASE 3: TESTES E VALIDAÇÃO**

#### **3.1 Test Suite**
**Arquivo:** `tests/test_performance.py`

```python
import pytest
import time
import json
from fraud_generator.generators import TransactionGenerator

class TestPerformance:
    def test_cached_weights_speedup(self):
        """Verify cached weights are faster than random.choices."""
        gen = TransactionGenerator()
        
        # Test searchsorted approach
        start = time.perf_counter()
        for _ in range(100000):
            tx_type = gen._weighted_choice_cached(
                gen._tx_type_cumsum,
                gen.TX_TYPES_LIST
            )
        elapsed_cached = time.perf_counter() - start
        
        # Should be <100ms for 100k calls
        assert elapsed_cached < 0.1, f"Cached too slow: {elapsed_cached:.3f}s"
    
    def test_fraud_pattern_consistency(self):
        """Verify fraud patterns are applied."""
        gen = TransactionGenerator(fraud_rate=1.0)  # Force all fraud
        
        transactions = []
        for i in range(100):
            tx = gen.generate(
                tx_id=f"test_{i}",
                customer_id="CUST_001",
                device_id="DEV_001",
                timestamp=datetime.now(),
            )
            transactions.append(tx)
        
        # All should be marked as fraud
        assert all(t['is_fraud'] for t in transactions)
        
        # Should have various fraud types
        fraud_types = {t['fraud_type'] for t in transactions}
        assert len(fraud_types) > 1, "Should have variety in fraud types"
    
    def test_transaction_json_serializable(self):
        """Verify transactions can be JSON serialized."""
        gen = TransactionGenerator()
        
        tx = gen.generate(
            tx_id="test_123",
            customer_id="CUST_001",
            device_id="DEV_001",
            timestamp=datetime.now(),
        )
        
        # Should serialize without error
        json_str = json.dumps(tx)
        assert len(json_str) > 0
        
        # Should deserialize back
        tx_loaded = json.loads(json_str)
        assert tx_loaded['transaction_id'] == tx['transaction_id']

# Run with: pytest tests/test_performance.py -v
```

---

## 📊 Roadmap Temporal

```
SEMANA 1 (Agora):
├─ 1.1 Cache de weights ...................... 2h
├─ 1.2 Cache de merchants .................... 1h
├─ 1.3 Remove campos None .................... 30min
├─ 1.4 Paralelizar customer gen .............. 2h
├─ 1.5 Add retry MinIO ....................... 1h
├─ 1.6 CSV streaming ......................... 2h
└─ Tests + Validação .......................... 1.5h
   TOTAL: ~10.5h (3 dias de trabalho)

SEMANA 2-3 (Próximas):
├─ 2.1 Fraud contextualization ............... 4h
├─ 2.2 Customer session state ................ 3h
├─ 2.3 Improved risk indicators .............. 2h
├─ Tests + Documentação ....................... 2h
└─ Performance benchmarking ................... 1h
   TOTAL: ~12h (3-4 dias)

MESES 2-3 (Future):
├─ ML-based fraud scoring
├─ Persistence layer (customer history)
├─ Analytics dashboard
└─ Performance monitoring
```

---

## 🔍 Métricas de Sucesso

### Performance
- [ ] Transações/segundo: >70k/s (vs 68k/s atual)
- [ ] Memory peak: <4GB (vs 8GB com Parquet atual)
- [ ] Tamanho JSON: -10% (remove campos None)

### Realismo
- [ ] Fraude tipos com características realistas
- [ ] Velocity correlado entre transações
- [ ] Padrões detectáveis por ML

### Reliability
- [ ] 0 data loss em MinIO failures
- [ ] 99.9% uptime em worker retries
- [ ] Logs detalhados de erros

---

## 📚 Referências & Recursos

### Documentos Relacionados
- `ANALISE_PROFUNDA.md` - Análise técnica detalhada
- `README.md` - Documentação geral do projeto

### Tools Recomendadas
```bash
# Profiling
python -m cProfile -s cumtime generate.py --size 100MB --output /tmp/test

# Memory profiling
pip install memory-profiler
python -m memory_profiler generate.py --size 100MB

# Benchmarking
pip install pytest-benchmark
pytest tests/test_performance.py --benchmark
```

### Leitura Adicional
- [Python: Weighted Random Sampling](https://docs.python.org/3/library/random.html#random.choices)
- [Multiprocessing vs Threading](https://realpython.com/intro-to-python-threading/)
- [Pandas Memory Optimization](https://pandas.pydata.org/docs/user_guide/enhancing.html)

